from pathlib import Path
common=(Path(__file__).with_name('ui-test-dnd.py')).read_text().split('\ntry:\n wait(lambda:item')[0]
exec(common.replace("folder=base/'dnd-fixture'","folder=base/'edge-fixture'"))
from PIL import ImageGrab,ImageStat,ImageChops,Image

def contrast(box):
 crop=ImageGrab.grab().crop(box).convert('RGB');return sum(ImageStat.Stat(ImageChops.difference(crop,Image.new('RGB',crop.size,'white'))).mean)
try:
 wait(lambda:item('alpha.txt'),'initial files',45)
 wid=run('search','--onlyvisible','--class','org.gnome.Nautilus').splitlines()[0]
 run('windowsize',wid,900,650);run('windowmove',wid,0,0);run('windowfocus',wid);time.sleep(.5)
 click('alpha.txt');r=rect(tile('alpha.txt'));box=(r.x+25,r.y+8,r.x+r.width-25,r.y+70);before=contrast(box)
 key('ctrl+x');time.sleep(.3);key('ctrl+r');time.sleep(.7)
 assert contrast(box)<before*.75
 passed('cut opacity persists after reloading the folder')
 go(folder/'destination');key('ctrl+v')
 wait(lambda:(folder/'destination'/'alpha.txt').exists() and not (folder/'alpha.txt').exists(),'cut paste')
 key('alt+Left');key('ctrl+z');wait(lambda:(folder/'alpha.txt').exists(),'undo cut move');time.sleep(.5)
 click('alpha.txt');r=rect(tile('alpha.txt'));box=(r.x+25,r.y+8,r.x+r.width-25,r.y+70)
 assert contrast(box)>before*.85
 passed('cut/paste uses normal move operations and undo restores full opacity')
 for i in range(100):(folder/f'long-{i:03}.txt').write_text('scroll fixture')
 key('ctrl+r');time.sleep(.7)
 # Scroll while drawing down from a blank gap above/left of the first tile.
 r=rect(tile('alpha.txt'));start=(r.x-3,r.y+3)
 run('mousemove',*start,'mousedown',1);time.sleep(.1)
 for step in range(1,16):
  run('mousemove',round(start[0]+(860-start[0])*step/15),round(start[1]+(625-start[1])*step/15));time.sleep(.03)
 time.sleep(2);screenshot('autoscroll-selection.png');run('mouseup',1);time.sleep(.3)
 names=selected();assert len(names)>24,(len(names),names)
 assert not visible(item('alpha.txt')) if item('alpha.txt') else True
 passed('rectangle selection scrolls through long folders and includes off-screen rows')
 print('ALL EDGE TESTS PASSED',flush=True)
finally:
 subprocess.run([sys.argv[1],'--quit'],capture_output=True,timeout=10)
