from pathlib import Path
common=(Path(__file__).with_name('ui-test-dnd.py')).read_text().split('\ntry:\n wait(lambda:item')[0]
exec(common.replace("folder=base/'dnd-fixture'","folder=base/'band-lifecycle-fixture'"))
try:
 wait(lambda:item('alpha.txt'),'initial files',45)
 wid=run('search','--onlyvisible','--class','org.gnome.Nautilus').splitlines()[0]
 run('windowsize',wid,900,650);run('windowmove',wid,0,0);run('windowfocus',wid);time.sleep(.5)
 for iteration in range(20):
  r=rect(tile('alpha.txt'));run('mousemove',r.x-3,r.y+r.height+3,'mousedown',1)
  run('mousemove',r.x+r.width+3,r.y-3,'mouseup',1)
  time.sleep(.08)
  assert selected()==['alpha.txt'],(iteration,selected())
 passed('20 rapid drag/release cycles flush pending frame and retain exact selection')
 r=rect(tile('alpha.txt'));run('mousemove',r.x-3,r.y+r.height+3,'mousedown',1,'mousemove',r.x+r.width+3,r.y-3);time.sleep(.1)
 (folder/'beta.txt').unlink();(folder/'new-during-drag.txt').write_text('new')
 run('windowsize',wid,1100,700);time.sleep(.5)
 run('mousemove',800,400);time.sleep(.15);run('key','Escape');run('mouseup',1);time.sleep(.3)
 names=selected();assert all((folder/n).exists() for n in names),names
 assert process.poll() is None
 passed('resize and directory mutation during drag leave only existing selections and no stale GTK access')
 r=rect(tile('alpha.txt'));run('mousemove',r.x-3,r.y+r.height+3,'mousedown',1,'mousemove',700,400);time.sleep(.1)
 key('ctrl+w');run('mouseup',1);time.sleep(.3)
 passed('closing an active gesture releases pending frame and cached objects')
 print('ALL LIFECYCLE TESTS PASSED')
finally:subprocess.run([sys.argv[1],'--quit'],capture_output=True,timeout=10)
