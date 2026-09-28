#ifndef UDT_SELECTION_H
#define UDT_SELECTION_H
#include <stddef.h>
#include <stdint.h>
typedef struct { double x,y,width,height; uint8_t initial,reserved[7]; } UdtRect;
typedef struct { double left,top,right,bottom; uint32_t flags,reserved; } UdtQuery;
/* Main-thread, nonoverlapping caller-owned buffers. No pointers retained. */
#ifdef __cplusplus
extern "C" {
#endif
int32_t udt_select(const UdtRect *rects,size_t n,UdtQuery query,uint8_t *out);
#ifdef __cplusplus
}
#define UDT_STATIC_ASSERT static_assert
#else
#define UDT_STATIC_ASSERT _Static_assert
#endif
UDT_STATIC_ASSERT(sizeof(UdtRect)==40,"Rust/C rectangle ABI mismatch");
UDT_STATIC_ASSERT(sizeof(UdtQuery)==40,"Rust/C query ABI mismatch");
#endif
