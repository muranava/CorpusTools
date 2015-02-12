
#import sys
#import vispy.mpl_plot as plt
#from PyQt5.QtWidgets import (QMainWindow, QLayout, QHBoxLayout, QLabel, QAction,
                                #QApplication)
#app = QApplication(sys.argv)
#win = QMainWindow()
#plt.plot([1,2,3,4], [1,4,9,16])
#vispyCanvas=plt.show()[0]
#win.setCentralWidget(vispyCanvas.native)
#win.show()
#sys.exit(app.exec_())


#import numpy as np
from vispy import app
#from vispy import gloo
#app.use_app(backend_name='PyQt5')

c = app.Canvas(app='PyQt5')
print(c.native)

#vertex = """
#attribute vec2 a_position;
#void main (void)
#{
    #gl_Position = vec4(a_position, 0.0, 1.0);
#}
#"""

#fragment = """
#void main()
#{
    #gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
#}
#"""

#program = gloo.Program(vertex, fragment)

#program['a_position'] = np.c_[
        #np.linspace(-1.0, +1.0, 1000),
        #np.random.uniform(-0.5, +0.5, 1000)]

#@c.connect
#def on_resize(event):
    #gloo.set_viewport(0, 0, *event.size)

#@c.connect
#def on_draw(event):
    #gloo.clear((1,1,1,1))
    #program.draw('line_strip')

c.show()
app.run()

