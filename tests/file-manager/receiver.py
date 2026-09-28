import gi,json,sys
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,Gdk
w=Gtk.Window(title='DnD Test Receiver')
w.set_default_size(350,300)
w.move(1000,100)
w.add(Gtk.Label(label='Drop test files here'))
w.drag_dest_set(Gtk.DestDefaults.ALL,[Gtk.TargetEntry.new('text/uri-list',0,0)],Gdk.DragAction.COPY)
def got(widget,ctx,x,y,data,info,time):
 with open(sys.argv[1],'w') as f:json.dump(data.get_uris(),f)
 Gtk.drag_finish(ctx,True,False,time)
w.connect('drag-data-received',got)
w.show_all()
Gtk.main()
