#include "../../src/selection-core/selection.h"
#include <vector>
#include <chrono>
#include <cstdio>
__attribute__((noinline)) void cpp_select(const UdtRect* rs,size_t n,UdtQuery q,uint8_t* out) {
 for(size_t i=0;i<n;++i){const auto&r=rs[i];bool h=q.flags&1 ? q.right>=r.x&&q.left<=r.x+r.width&&q.bottom>=r.y&&q.top<=r.y+r.height:q.left<=r.x&&q.right>=r.x+r.width&&q.top<=r.y&&q.bottom>=r.y+r.height;out[i]=q.flags&8?r.initial:q.flags&2?bool(r.initial)!=h:q.flags&4?bool(r.initial)||h:h;}
}
volatile unsigned sink=0;
int main(){std::vector<UdtRect> r(5000);std::vector<uint8_t> out(r.size());for(size_t i=0;i<r.size();i++)r[i]={double(i%20*100),double(i/20*100),90,90,uint8_t(i%3==0),{0}};
 for(int repeat=0;repeat<4;repeat++)for(int lang=0;lang<2;lang++){
 auto start=std::chrono::steady_clock::now();for(int k=0;k<20000;k++){UdtQuery q={20,20,double(200+k%1500),double(500+k%20000),uint32_t(k%16),0};if(lang)udt_select(r.data(),r.size(),q,out.data());else cpp_select(r.data(),r.size(),q,out.data());sink+=out[k%out.size()];}
 auto ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();printf("%s %.3f ms\n",lang?"Rust FFI":"C++",ms);
 }
}
