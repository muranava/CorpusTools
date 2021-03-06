
import os
import codecs

from .imports import *
from .widgets import DirectoryWidget

class BasePane(QWidget):
    """Abstract, don't use"""

    prev_state = {}

    def get_current_state(self):
        return None

    def is_changed(self):
        return self.get_current_state() != self.prev_state

    def validate(self):
        pass


class StoragePane(BasePane):
    def __init__(self, setting_dict):
        BasePane.__init__( self )

        layout = QFormLayout()

        self.storageDirectoryWidget = DirectoryWidget()

        layout.addRow(QLabel('Storage directory:'),self.storageDirectoryWidget)

        self.autosaveCheck = QCheckBox()

        layout.addRow(QLabel('Auto save:'),self.autosaveCheck)

        self.setLayout(layout)

        #set up defaults

        #storageDirectory = codecs.getdecoder("unicode_escape")(setting_dict['storage'])[0]
        storageDirectory = setting_dict['storage']

        autosave = setting_dict['autosave']

        self.storageDirectoryWidget.setPath(storageDirectory)

        self.autosaveCheck.setChecked(autosave)

        self.prev_state = setting_dict

    def validate(self):
        root = os.path.dirname(self.storageDirectoryWidget.value())
        if not os.path.exists(root):
            raise(Exception('The specified directory\'s parent directory ({}) does not exist.'.format(root)))

    def get_current_state(self):
        setting_dict = {}

        setting_dict['storage'] = self.storageDirectoryWidget.value()
        setting_dict['autosave'] = int(self.autosaveCheck.isChecked())

        return setting_dict



class DisplayPane(BasePane):
    def __init__(self, setting_dict):
        BasePane.__init__( self )

        layout = QFormLayout()

        self.sigfigWidget = QLineEdit()

        layout.addRow(QLabel('Number of displayed decimal places:'),self.sigfigWidget)

        self.setLayout(layout)

        #set up defaults

        sigfigs = setting_dict['sigfigs']

        self.sigfigWidget.setText(str(sigfigs))

        self.prev_state = setting_dict

    def validate(self):
        try:
            t = int(self.sigfigWidget.text())
        except ValueError:
            raise(Exception('Number of significant figures requires an integer'))

    def get_current_state(self):
        setting_dict = {}

        setting_dict['sigfigs'] = int(self.sigfigWidget.text())

        return setting_dict

class ProcessingPane(BasePane):
    def __init__(self, setting_dict):
        BasePane.__init__( self )

        layout = QFormLayout()

        self.usemultiCheck = QCheckBox()

        layout.addRow(QLabel('Use multiprocessing (where available)'),self.usemultiCheck)

        self.numcoresWidget = QLineEdit()

        layout.addRow(QLabel('Number of cores to use\n(Set to 0 to use 3/4 of the available cores):'),self.numcoresWidget)

        self.setLayout(layout)

        #set up defaults

        use_multi = setting_dict['use_multi']
        num_cores = setting_dict['num_cores']

        self.usemultiCheck.setChecked(use_multi)

        self.numcoresWidget.setText(str(num_cores))

        self.prev_state = setting_dict

    def get_current_state(self):
        setting_dict = {}

        setting_dict['use_multi'] = int(self.usemultiCheck.isChecked())
        setting_dict['num_cores'] = int(self.numcoresWidget.text())

        return setting_dict

class Settings(object):

    key_to_ini = {'storage': ('storage/directory',os.path.normpath(os.path.join(
                                            os.path.expanduser('~/Documents'),'PCT','CorpusTools'))),
                    'autosave': ('storage/autosave',1),
                    'praatpath': ('storage/praat',''),
                    'size':('display/size', QSize(270, 225)),
                    'pos': ('display/pos', QPoint(50, 50)),
                    'sigfigs': ('display/sigfigs',3),
                    'warnings': ('display/warnings',1),
                    'tooltips': ('display/tooltips',1),
                    'use_multi': ('multiprocessing/enabled',0),
                    'num_cores': ('multiprocessing/numcores',1)}

    storage_setting_keys = ['storage','autosave']

    display_setting_keys = ['sigfigs', 'warnings','tooltips']

    processing_setting_keys = ['use_multi','num_cores']

    def __init__(self):
        self.qs = QSettings("PCT","Phonological CorpusTools")
        #self.qs.setFallbacksEnabled(False)
        self.check_storage()

    def error_directory(self):
        return os.path.join(self['storage'],'ERRORS')

    def check_storage(self):
        if not os.path.exists(self['storage']):
            os.makedirs(self['storage'])
        LOG_DIR = os.path.join(self['storage'],'LOG')
        ERROR_DIR = os.path.join(self['storage'],'ERRORS')
        TMP_DIR = os.path.join(self['storage'],'TMP')
        CORPUS_DIR = os.path.join(self['storage'],'CORPUS')
        FEATURE_DIR = os.path.join(self['storage'],'FEATURE')
        if not os.path.exists(LOG_DIR):
            os.mkdir(LOG_DIR)
        if not os.path.exists(ERROR_DIR):
            os.mkdir(ERROR_DIR)
        if not os.path.exists(TMP_DIR):
            os.mkdir(TMP_DIR)

        if not os.path.exists(CORPUS_DIR):
            os.mkdir(CORPUS_DIR)

        if not os.path.exists(FEATURE_DIR):
            os.mkdir(FEATURE_DIR)

    def __getitem__(self, key):

        mapped_key = self.key_to_ini[key]
        if isinstance(mapped_key, list):
            return tuple(type(d)(self.qs.value(k,d)) for k, d in mapped_key)
        else:
            inikey, default = mapped_key
            return type(default)(self.qs.value(inikey,default))

    def __setitem__(self, key, value):
        mapped_key = self.key_to_ini[key]
        if isinstance(mapped_key, list):
            if not isinstance(value,list) and not isinstance(value,tuple):
                raise(KeyError)
            if len(mapped_key) != len(value):
                raise(KeyError)
            for i,(k, d) in enumerate(mapped_key):
                self.qs.setValue(k,value[i])
        else:
            inikey, default = mapped_key
            self.qs.setValue(inikey,value)

    def sync(self):
        self.qs.sync()

    def update(self,setting_dict):
        for k,v in setting_dict.items():
            self[k] = v

    def get_storage_settings(self):
        out = {x: self[x] for x in self.storage_setting_keys}
        return out

    def get_display_settings(self):
        out = {x: self[x] for x in self.display_setting_keys}
        return out

    def get_processing_settings(self):
        out = {x: self[x] for x in self.processing_setting_keys}
        return out

class PreferencesDialog(QDialog):

    def __init__(self, parent, settings):
        QDialog.__init__( self, parent )

        self.settings = settings

        tabWidget = QTabWidget()

        #Storage
        self.storeWidget = StoragePane(self.settings.get_storage_settings())

        tabWidget.addTab(self.storeWidget,'Storage')

        #Display
        self.displayWidget = DisplayPane(self.settings.get_display_settings())

        tabWidget.addTab(self.displayWidget,'Display')

        #Processing
        self.processingWidget = ProcessingPane(self.settings.get_processing_settings())

        tabWidget.addTab(self.processingWidget,'Processing')

        layout = QVBoxLayout()
        layout.addWidget(tabWidget)
        #Accept cancel
        self.acceptButton = QPushButton('Ok')
        self.cancelButton = QPushButton('Cancel')

        self.acceptButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        hbox = QHBoxLayout()
        hbox.addWidget(self.acceptButton)
        hbox.addWidget(self.cancelButton)
        ac = QWidget()
        ac.setLayout(hbox)
        layout.addWidget(ac)

        self.setLayout(layout)

        self.setWindowTitle('Edit preferences')

    def accept(self):
        try:
            self.storeWidget.validate()
            self.displayWidget.validate()
            self.processingWidget.validate()
        except Exception as e:
            reply = QMessageBox.critical(self,
                    "Invalid information", str(e))
            return

        self.settings.update(self.storeWidget.get_current_state())
        self.settings.update(self.displayWidget.get_current_state())
        self.settings.update(self.processingWidget.get_current_state())
        self.settings.check_storage()
        QDialog.accept(self)
