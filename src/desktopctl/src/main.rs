#![forbid(unsafe_code)]
use std::{env,fs,io::{Read,BufReader},path::Path,process::{Command,ExitCode}};
use sha2::{Digest,Sha256};
fn hash(path:&Path)->Result<String,String>{
 let mut f=BufReader::new(fs::File::open(path).map_err(|e|format!("{}: {e}",path.display()))?);let mut h=Sha256::new();let mut buffer=[0u8;65536];
 loop{let n=f.read(&mut buffer).map_err(|e|e.to_string())?;if n==0{break}h.update(&buffer[..n]);}Ok(format!("{:x}",h.finalize()))
}
fn check(root:&Path)->Result<(),String>{
 let list=fs::read_to_string(root.join("SHA256SUMS")).map_err(|e|e.to_string())?;let mut n=0;
 for line in list.lines(){let (digest,name)=line.split_once("  ").ok_or("invalid checksum line")?;
  if digest.len()!=64 || !digest.bytes().all(|b|b.is_ascii_hexdigit()) {return Err("invalid digest".into())}
  let file=root.join(name).canonicalize().map_err(|e|format!("{name}: {e}"))?;
  if !file.starts_with(root) || hash(&file)?!=digest {return Err(format!("校验失败: {name}"))}n+=1;
 }println!("{n} 个文件校验通过");Ok(())
}
fn execute(program:&str,args:&[String],root:&Path)->Result<(),String>{
 let status=Command::new(program).args(args).current_dir(root).status().map_err(|e|e.to_string())?;
 if status.success(){Ok(())}else{Err(format!("{program} 返回 {status}"))}
}
fn main()->ExitCode{match work(){Ok(())=>ExitCode::SUCCESS,Err(e)=>{eprintln!("desktopctl: {e}");ExitCode::FAILURE}}}
fn work()->Result<(),String>{
 let exe=env::current_exe().map_err(|e|e.to_string())?;
 let root=exe.parent().and_then(Path::parent).ok_or("binary must be in bin/")?.canonicalize().map_err(|e|e.to_string())?;
 let mut args:Vec<String>=env::args().skip(1).collect();if args.is_empty(){args.push("help".into());}
 match args[0].as_str(){
  "help"|"--help"=>println!("desktopctl check | status | install <all|file-manager|terminal|sogou> [--check] [--selection-style] [--project-menu] | restore <backup> [--apply] | sync <user@host:path>"),
  "check"=>{if args.len()!=1{return Err("check takes no arguments".into())}check(&root)?;},
  "status"=>{
   let config:serde_json::Value=serde_json::from_str(&fs::read_to_string(root.join("components.json")).map_err(|e|e.to_string())?).map_err(|e|e.to_string())?;
   println!("目标平台: {}",config["platform"]);println!("文件管理器目标版本: {}",config["file_manager"]["version"]);
   execute("/usr/bin/python3",&["scripts/verify.py".into(),"--status".into()],&root)?;
  },
  "install"|"restore"=>{
   check(&root)?;
   let script=if args[0]=="install"{"scripts/install.py"}else{"scripts/restore-config.py"};
   let mut forwarded=vec![script.into()];forwarded.extend(args.into_iter().skip(1));execute("/usr/bin/python3",&forwarded,&root)?;
  },
  "sync"=>{
   if args.len()!=2{return Err("sync requires one user@host:path".into())}
   let target=&args[1];let (host,path)=target.split_once(':').ok_or("expected user@host:path")?;
   if host.is_empty() || path.is_empty() || host.starts_with('-') || !host.bytes().all(|c|c.is_ascii_alphanumeric()||b"@.-_".contains(&c)) || path.contains(':') || path.chars().any(char::is_control){return Err("invalid remote destination".into())}
   check(&root)?;execute("rsync",&["-a".into(),"--protect-args".into(),"--".into(),format!("{}/",root.display()),target.clone()],&root)?;
  },
  other=>return Err(format!("unknown command: {other}"))
 }Ok(())
}
