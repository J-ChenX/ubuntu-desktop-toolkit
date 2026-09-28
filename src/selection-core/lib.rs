//! Allocation-free selection kernel. GTK ownership stays entirely in the adapter.
#![deny(unsafe_op_in_unsafe_fn)]
#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct Rect { pub x:f64, pub y:f64, pub width:f64, pub height:f64, pub initial:u8, pub reserved:[u8;7] }
#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct Query { pub left:f64, pub top:f64, pub right:f64, pub bottom:f64, pub flags:u32, pub reserved:u32 }
/// Pure safe Rust: no GTK references, allocation, callbacks, or global state.
pub fn select(rects:&[Rect], q:Query, out:&mut [u8]) -> bool {
    if rects.len()!=out.len() || q.flags & !15 != 0 ||
       ![q.left,q.top,q.right,q.bottom].iter().all(|x|x.is_finite()) || q.left>q.right || q.top>q.bottom {return false;}
    for (r,dst) in rects.iter().zip(out.iter_mut()) {
        let hit=if q.flags&1!=0 {q.right>=r.x && q.left<=r.x+r.width && q.bottom>=r.y && q.top<=r.y+r.height}
                else {q.left<=r.x && q.right>=r.x+r.width && q.top<=r.y && q.bottom>=r.y+r.height};
        let initial=r.initial!=0;
        *dst=if q.flags&8!=0 {initial} else if q.flags&2!=0 {initial!=hit} else if q.flags&4!=0 {initial||hit} else {hit} as u8;
    }
    true
}
/// # Safety
/// Caller owns `n` initialized Rects and `n` writable bytes, valid until return.
/// Buffers must not overlap, be concurrently mutated, or contain GTK pointers.
/// No pointer is retained. Null is accepted only for zero length.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn udt_select(rects:*const Rect,n:usize,q:Query,out:*mut u8)->i32 {
    if n==0 {return 1;}
    if n>10_000_000 || rects.is_null() || out.is_null() || (rects as usize)%std::mem::align_of::<Rect>()!=0 {return 0;}
    let Some(end_r)=(rects as usize).checked_add(n*std::mem::size_of::<Rect>()) else {return 0;};
    let Some(end_o)=(out as usize).checked_add(n) else {return 0;};
    if (rects as usize)<end_o && (out as usize)<end_r {return 0;}
    // SAFETY: range, alignment and non-overlap checked here; allocation validity
    // and exclusive access are required from the GTK adapter, on its main thread.
    let input=unsafe {std::slice::from_raw_parts(rects,n)};
    let output=unsafe {std::slice::from_raw_parts_mut(out,n)};
    // Never unwind through C. Algorithm has no indexing or allocation; catch also
    // protects future changes. OOM/abort outside unwinding is not recoverable.
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(||select(input,q,output))).unwrap_or(false) as i32
}
#[cfg(test)] mod tests {
 use super::*;
 #[test] fn exhaustive_geometry_and_modifiers(){
  for initial in [0,1] {for x in -5..6 {for y in -5..6 {for flags in 0..16 {
   let r=Rect{x:x as f64,y:y as f64,width:3.,height:4.,initial,reserved:[0;7]};
   let q=Query{left:0.,top:0.,right:4.,bottom:5.,flags,reserved:0};let mut out=[9];
   assert!(select(&[r],q,&mut out));
   let overlap=!(r.x>4. || r.x+3.<0. || r.y>5. || r.y+4.<0.);
   let contained=r.x>=0. && r.y>=0. && r.x+3.<=4. && r.y+4.<=5.;
   let hit=if flags&1!=0{overlap}else{contained};let start=initial!=0;
   assert_eq!(out[0],(if flags&8!=0{start}else if flags&2!=0{start^hit}else if flags&4!=0{start||hit}else{hit}) as u8);
  }}}}
 }
 #[test] fn rejects_invalid_queries(){let r=Rect{x:0.,y:0.,width:1.,height:1.,initial:0,reserved:[0;7]};let mut out=[7];
  for left in [f64::NAN,f64::INFINITY,2.] {assert!(!select(&[r],Query{left,top:0.,right:1.,bottom:1.,flags:0,reserved:0},&mut out));assert_eq!(out,[7]);}
 }
 #[test] fn ffi_rejects_null_and_alias(){let mut r=Rect{x:0.,y:0.,width:1.,height:1.,initial:0,reserved:[0;7]};let q=Query{left:0.,top:0.,right:1.,bottom:1.,flags:0,reserved:0};
  unsafe{assert_eq!(udt_select(std::ptr::null(),1,q,std::ptr::null_mut()),0);assert_eq!(udt_select(&r,1,q,(&mut r as *mut Rect).cast()),0);assert_eq!(udt_select(std::ptr::null(),0,q,std::ptr::null_mut()),1);}
 }
}
