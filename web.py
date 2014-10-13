import voptiq
from bottle import template, static_file, request

class WebApp(object):
  STATIC_DIR = 'assets/'

  def __init__(self, delegate):
    self.delegate = delegate
    self.cache = {}

  def __call__(self, environ, start_response):
    return self.delegate(environ, start_response)

  def register(self):
    self.delegate.route('/')(self.home)
    self.delegate.route('/s/:path#.+#')(self.static)
    self.delegate.route('/analyze')(self.analyze)

  def home(self):
    return template('home.html', path='', msg='', trace='')

  def static(self, path):
    return static_file(path, root=self.STATIC_DIR)

  def analyze(self):
    path = request.query.trace
    msg = trace = None
    if path:
      try:
        if path not in self.cache:
          self.cache[path] = voptiq.Trace.parse(path)
        trace = self.cache[path]
      except IOError:
        msg = dict(text='Unable to find trace file: [{}]'.format(path), kind='danger')
    return template('home.html', path=path, trace=trace, msg=msg)

  @classmethod
  def create(cls, module):
    wapp = WebApp(module)
    wapp.register()
    return wapp
