import os
import sys

from .imports import *

from .config import Settings, PreferencesDialog
from .views import (TableWidget, TreeWidget, DiscourseView, ResultsWindow,
                    LexiconView,PhonoSearchResults)
from .models import CorpusModel, ResultsModel, SpontaneousSpeechCorpusModel,DiscourseModel

from .corpusgui import (CorpusLoadDialog, AddTierDialog, AddAbstractTierDialog,
                        RemoveAttributeDialog,SubsetCorpusDialog, AddColumnDialog,
                        AddCountColumnDialog,
                        ExportCorpusDialog, AddWordDialog, CorpusSummary, save_binary)

from .featuregui import (FeatureMatrixManager, EditFeatureMatrixDialog,
                        ExportFeatureSystemDialog)

from .windows import SelfUpdateWorker

from .ssgui import SSDialog
from .asgui import ASDialog
from .flgui import FLDialog
from .fagui import FADialog
from .pdgui import PDDialog
from .ndgui import NDDialog
from .ppgui import PPDialog
from .psgui import PhonoSearchDialog
from .migui import MIDialog
from .klgui import KLDialog
from .helpgui import AboutDialog, HelpDialog

from . import pct_rc

class QApplicationMessaging(QApplication):
    messageFromOtherInstance = Signal(bytes)

    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self._key = 'PCT'
        self._timeout = 1000
        self._locked = False
        socket = QLocalSocket(self)
        socket.connectToServer(self._key, QIODevice.WriteOnly)
        if not socket.waitForConnected(self._timeout):
            self._server = QLocalServer(self)
            # noinspection PyUnresolvedReferences
            self._server.newConnection.connect(self.handleMessage)
            self._server.listen(self._key)
        else:
            self._locked = True
        socket.disconnectFromServer()

    def __del__(self):
        if not self._locked:
            self._server.close()

    def event(self, e):
        if e.type() == QEvent.FileOpen:
            self.messageFromOtherInstance.emit(bytes(e.file(), 'UTF-8'))
            return True
        else:
            return QApplication.event(self, e)

    def isRunning(self):
        return self._locked

    def handleMessage(self):
        socket = self._server.nextPendingConnection()
        if socket.waitForReadyRead(self._timeout):
            self.messageFromOtherInstance.emit(socket.readAll().data())

    def sendMessage(self, message):
        socket = QLocalSocket(self)
        socket.connectToServer(self._key, QIODevice.WriteOnly)
        socket.waitForConnected(self._timeout)
        socket.write(bytes(message, 'UTF-8'))
        socket.waitForBytesWritten(self._timeout)
        socket.disconnectFromServer()

class MainWindow(QMainWindow):

    def __init__(self,app):
        app.messageFromOtherInstance.connect(self.handleMessage)
        super(MainWindow, self).__init__()

        self.unsavedChanges = False

        self.settings = Settings()

        self.showWarnings = True
        self.showToolTips = True

        self.resize(self.settings['size'])
        self.move(self.settings['pos'])

        self.corpusTable = LexiconView(self)
        self.corpusTable.wordsChanged.connect(self.enableSave)
        self.corpusTable.wordToBeEdited.connect(self.editWord)
        self.corpusTable.columnRemoved.connect(self.enableSave)
        self.discourseTree = TreeWidget(self)
        self.discourseTree.newLexicon.connect(self.changeLexicon)
        self.discourseTree.hide()
        self.textWidget = DiscourseView(self)
        self.textWidget.hide()
        #font = QFont("Courier New", 14)
        #self.corpusTable.setFont(font)
        splitter = QSplitter()
        splitter.addWidget(self.discourseTree)
        splitter.addWidget(self.corpusTable)
        splitter.addWidget(self.textWidget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)
        self.wrapper = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(splitter)
        self.wrapper.setLayout(layout)
        self.setCentralWidget(self.wrapper)

        self.status = QLabel()
        self.status.setText("Ready")
        self.statusBar().addWidget(self.status, stretch=1)
        self.corpusStatus = QLabel()
        self.corpusStatus.setText("No corpus selected")
        self.statusBar().addWidget(self.corpusStatus)
        self.featureSystemStatus = QLabel()
        self.featureSystemStatus.setText("No feature system selected")
        self.statusBar().addWidget(self.featureSystemStatus)

        self.setWindowTitle("Phonological CorpusTools")
        self.createActions()
        self.createMenus()
        self.corpusModel = None

        self.FLWindow = None
        self.PDWindow = None
        self.FAWindow = None
        self.SSWindow = None
        self.ASWindow = None
        self.NDWindow = None
        self.PPWindow = None
        self.MIWindow = None
        self.KLWindow = None
        self.PhonoSearchWindow = None
        self.setMinimumWidth(self.menuBar().sizeHint().width())

    def sizeHint(self):
        sz = QMainWindow.sizeHint(self)
        minWidth = self.menuBar().sizeHint().width()
        if sz.width() < minWidth:
            sz.setWidth(minWidth)
        if sz.height() < 400:
            sz.setHeight(400)
        return sz

    def handleMessage(self):
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        #self.raise_()
        #self.show()
        self.activateWindow()

    def check_for_unsaved_changes(function):
        def do_check(self):
            if self.unsavedChanges:
                reply = QMessageBox()
                reply.setWindowTitle("Unsaved changes")
                reply.setIcon(QMessageBox.Warning)
                reply.setText("The currently loaded corpus ('{}') has unsaved changes.".format(self.corpus.name))
                reply.setInformativeText("Do you want to save your changes?")

                reply.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
                reply.setDefaultButton(QMessageBox.Save)
                ret = reply.exec_()
                if ret == QMessageBox.Save:
                    self.saveCorpus()
                elif ret == QMessageBox.Cancel:
                    return
            function(self)

        return do_check

    def check_for_empty_corpus(function):
        def do_check(self):
            if self.corpusModel is None or self.corpusModel.corpus is None:
                reply = QMessageBox.critical(self,
                        "Missing corpus", "There is no corpus loaded.")
                return
            else:
                function(self)
        return do_check

    def check_for_transcription(function):
        def do_check(self):
            if not self.corpusModel.corpus.has_transcription:
                reply = QMessageBox.critical(self,
                        "Missing transcription", "This corpus has no transcriptions, so the requested action cannot be performed.")
                return
            else:
                function(self)
        return do_check

    def enableSave(self):
        self.unsavedChanges = True
        self.saveCorpusAct.setEnabled(True)

    def editWord(self, row, word):
        dialog = AddWordDialog(self, self.corpusModel.corpus, word)
        if dialog.exec_():
            self.corpusModel.replaceWord(row, dialog.word)
            self.enableSave()

    def changeText(self):
        name = self.discourseTree.model().data(self.discourseTree.selectionModel().currentIndex(),Qt.DisplayRole)
        if hasattr(self.corpus, 'lexicon'):
            try:
                discourse = self.corpus.discourses[name]
            except KeyError:
                return
            self.textWidget.setModel(DiscourseModel(discourse, self.settings))

    def changeLexicon(self, c):
        self.corpusTable.setModel(CorpusModel(c, self.settings))
        self.corpusStatus.setText('Corpus: {}'.format(c.name))
        if c.specifier is not None:
            self.featureSystemStatus.setText('Feature system: {}'.format(c.specifier.name))
        else:
            self.featureSystemStatus.setText('No feature system selected')

    @check_for_unsaved_changes
    def loadCorpus(self):
        dialog = CorpusLoadDialog(self)
        result = dialog.exec_()
        if result:

            self.corpus = dialog.corpus
            if hasattr(self.corpus,'lexicon'):
                c = self.corpus.lexicon
                if hasattr(self.corpus,'discourses'):
                    self.discourseTree.show()
                    self.discourseTree.setModel(SpontaneousSpeechCorpusModel(self.corpus))
                    self.discourseTree.selectionModel().selectionChanged.connect(self.changeText)
                    self.showDiscoursesAct.setEnabled(True)
                    self.showDiscoursesAct.setChecked(True)
                    if self.textWidget.model() is not None:
                        self.textWidget.model().deleteLater()
                else:
                    self.textWidget.setModel(DiscourseModel(self.corpus, self.settings))
                    self.discourseTree.hide()
                    self.showDiscoursesAct.setEnabled(False)
                    self.showDiscoursesAct.setChecked(False)
                #self.discourseTree.selectionModel().select(self.discourseTree.model().createIndex(0,0))
                #self.discourseTree.resizeColumnToContents(0)
                self.corpusTable.selectTokens.connect(self.textWidget.highlightTokens)
                self.textWidget.selectType.connect(self.corpusTable.highlightType)
                self.textWidget.show()
                self.showTextAct.setEnabled(True)
                self.showTextAct.setChecked(True)
            else:
                c = self.corpus
                self.textWidget.hide()
                self.discourseTree.hide()
                self.showTextAct.setEnabled(False)
                self.showTextAct.setChecked(False)
                self.showDiscoursesAct.setEnabled(False)
                self.showDiscoursesAct.setChecked(False)
                if self.textWidget.model() is not None:
                    self.textWidget.model().deleteLater()
            self.corpusModel = CorpusModel(c, self.settings)
            self.corpusTable.setModel(self.corpusModel)
            self.corpusStatus.setText('Corpus: {}'.format(c.name))
            if c.specifier is not None:
                self.featureSystemStatus.setText('Feature system: {}'.format(c.specifier.name))
            else:
                self.featureSystemStatus.setText('No feature system selected')
            self.unsavedChanges = False
            self.saveCorpusAct.setEnabled(False)
        #dialog.deleteLater()

    def loadFeatureMatrices(self):
        dialog = FeatureMatrixManager(self)
        result = dialog.exec_()

    def subsetCorpus(self):
        dialog = SubsetCorpusDialog(self,self.corpusModel.corpus)
        result = dialog.exec_()
        if result:
            pass

    def saveCorpus(self):
        save_binary(self.corpus,os.path.join(
                        self.settings['storage'],'CORPUS',
                        self.corpus.name+'.corpus'))
        self.saveCorpusAct.setEnabled(False)
        self.unsavedChanges = False

    def exportCorpus(self):
        dialog = ExportCorpusDialog(self,self.corpusModel.corpus)
        result = dialog.exec_()
        if result:
            pass

    def exportFeatureMatrix(self):
        dialog = ExportFeatureSystemDialog(self,self.corpusModel.corpus)
        result = dialog.exec_()
        if result:
            pass

    def showPreferences(self):
        dialog = PreferencesDialog(self, self.settings)
        if dialog.exec_():
            self.settings = dialog.settings

    @check_for_empty_corpus
    @check_for_transcription
    def showFeatureSystem(self):
        dialog = EditFeatureMatrixDialog(self,self.corpusModel.corpus)
        if dialog.exec_():
            self.corpusModel.corpus.set_feature_matrix(dialog.specifier)
            if self.corpusModel.corpus.specifier is not None:
                self.featureSystemStatus.setText('Feature system: {}'.format(self.corpusModel.corpus.specifier.name))
            else:
                self.featureSystemStatus.setText('No feature system selected')
            if self.settings['autosave']:
                self.saveCorpus()
                self.saveCorpusAct.setEnabled(False)
            else:
                self.enableSave()

    @check_for_empty_corpus
    @check_for_transcription
    def createTier(self):
        dialog = AddTierDialog(self, self.corpusModel.corpus)
        if dialog.exec_():
            self.corpusModel.addTier(dialog.attribute, dialog.segList)
            if self.settings['autosave']:
                self.saveCorpus()
                self.saveCorpusAct.setEnabled(False)
            else:
                self.enableSave()
            self.adjustSize()

    @check_for_empty_corpus
    @check_for_transcription
    def createAbstractTier(self):
        dialog = AddAbstractTierDialog(self, self.corpusModel.corpus)
        if dialog.exec_():
            self.corpusModel.addAbstractTier(dialog.attribute, dialog.segList)
            if self.settings['autosave']:
                self.saveCorpus()
                self.saveCorpusAct.setEnabled(False)
            else:
                self.enableSave()
            self.adjustSize()

    @check_for_empty_corpus
    def createColumn(self):
        dialog = AddColumnDialog(self, self.corpusModel.corpus)
        if dialog.exec_():
            self.corpusModel.addColumn(dialog.attribute)
            if self.settings['autosave']:
                self.saveCorpus()
                self.saveCorpusAct.setEnabled(False)
            else:
                self.enableSave()

    @check_for_empty_corpus
    def createCountColumn(self):
        dialog = AddCountColumnDialog(self, self.corpusModel.corpus)
        if dialog.exec_():
            self.corpusModel.addCountColumn(dialog.attribute, dialog.sequenceType, dialog.segList)
            if self.settings['autosave']:
                self.saveCorpus()
                self.saveCorpusAct.setEnabled(False)
            else:
                self.enableSave()

    @check_for_empty_corpus
    @check_for_transcription
    def removeAttribute(self):
        dialog = RemoveAttributeDialog(self, self.corpusModel.corpus)
        if dialog.exec_():
            self.corpusModel.removeAttributes(dialog.tiers)
            self.adjustSize()

            if self.settings['autosave']:
                self.saveCorpus()
                self.saveCorpusAct.setEnabled(False)
            else:
                self.enableSave()

    @check_for_empty_corpus
    def stringSim(self):
        dialog = SSDialog(self, self.corpusModel,self.showToolTips)
        result = dialog.exec_()
        if result:
            if self.SSWindow is not None and dialog.update and self.SSWindow.isVisible():
                self.SSWindow.table.model().addData(dialog.results)
            else:
                self.SSWindow = ResultsWindow('String similarity results',dialog,self)
                self.SSWindow.show()
                self.showSSResults.triggered.connect(self.SSWindow.raise_)
                self.showSSResults.triggered.connect(self.SSWindow.activateWindow)
                self.SSWindow.rejected.connect(lambda: self.showSSResults.setVisible(False))
                self.showSSResults.setVisible(True)

    @check_for_empty_corpus
    @check_for_transcription
    def freqOfAlt(self):
        dialog = FADialog(self, self.corpusModel.corpus,self.showToolTips)
        result = dialog.exec_()
        if result:
            if self.FAWindow is not None and dialog.update and self.FAWindow.isVisible():
                self.FAWindow.table.model().addRows(dialog.results)
            else:
                self.FAWindow = ResultsWindow('Frequency of alternation results',dialog,self)
                self.FAWindow.show()
                self.showFAResults.triggered.connect(self.FAWindow.raise_)
                self.showFAResults.triggered.connect(self.FAWindow.activateWindow)
                self.FAWindow.rejected.connect(lambda: self.showFAResults.setVisible(False))
                self.showFAResults.setVisible(True)

    @check_for_empty_corpus
    @check_for_transcription
    def predOfDist(self):
        dialog = PDDialog(self, self.corpusModel.corpus,self.showToolTips)
        result = dialog.exec_()
        if result:
            if self.PDWindow is not None and self.PDWindow.isVisible():
                self.PDWindow.table.model().addRows(dialog.results)
            else:
                self.PDWindow = ResultsWindow('Predictability of distribution results',dialog,self)
                self.PDWindow.show()
                self.showPDResults.triggered.connect(self.PDWindow.raise_)
                self.showPDResults.triggered.connect(self.PDWindow.activateWindow)
                self.PDWindow.rejected.connect(lambda: self.showPDResults.setVisible(False))
                self.showPDResults.setVisible(True)

    @check_for_empty_corpus
    @check_for_transcription
    def funcLoad(self):
        dialog = FLDialog(self, self.corpusModel.corpus,self.showToolTips)
        result = dialog.exec_()
        if result:
            if self.FLWindow is not None and dialog.update and self.FLWindow.isVisible():
                self.FLWindow.table.model().addRows(dialog.results)
            else:
                self.FLWindow = ResultsWindow('Functional load results',dialog,self)
                self.FLWindow.show()
                self.showFLResults.triggered.connect(self.FLWindow.raise_)
                self.showFLResults.triggered.connect(self.FLWindow.activateWindow)
                self.FLWindow.rejected.connect(lambda: self.showFLResults.setVisible(False))
                self.showFLResults.setVisible(True)

    def kullbackLeibler(self):
        dialog = KLDialog(self, self.corpusModel.corpus, self.showToolTips)
        result = dialog.exec_()
        if result:
            if self.KLWindow is not None and dialog.update and self.KLWindow.isVisible():
                self.KLWindow.table.model().addRows(dialog.results)
            else:
                self.KLWindow = ResultsWindow('Kullback Leibler results', dialog, self)
                self.KLWindow.show()
                self.showKLResults.triggered.connect(self.KLWindow.raise_)
                self.showKLResults.triggered.connect(self.KLWindow.activateWindow)
                self.KLWindow.rejected.connect(lambda: self.showKLResults.setVisible(False))
                self.showKLResults.setVisible(True)

    @check_for_empty_corpus
    @check_for_transcription
    def mutualInfo(self):
        dialog = MIDialog(self, self.corpusModel.corpus,self.showToolTips)
        result = dialog.exec_()
        if result:
            if self.MIWindow is not None and dialog.update and self.MIWindow.isVisible():
                self.MIWindow.table.model().addRows(dialog.results)
            else:
                self.MIWindow = ResultsWindow('Mutual information results',dialog,self)
                self.MIWindow.show()
                self.showMIResults.triggered.connect(self.MIWindow.raise_)
                self.showMIResults.triggered.connect(self.MIWindow.activateWindow)
                self.MIWindow.rejected.connect(lambda: self.showMIResults.setVisible(False))
                self.showMIResults.setVisible(True)

    def acousticSim(self):
        dialog = ASDialog(self,self.showToolTips)
        result = dialog.exec_()
        if result:
            if self.ASWindow is not None and dialog.update and self.ASWindow.isVisible():
                self.ASWindow.table.model().addRows(dialog.results)
            else:
                self.ASWindow = ResultsWindow('Acoustic similarity results',dialog,self)
                self.ASWindow.show()
                self.showASResults.triggered.connect(self.ASWindow.raise_)
                self.showASResults.triggered.connect(self.ASWindow.activateWindow)
                self.ASWindow.rejected.connect(lambda: self.showASResults.setVisible(False))
                self.showASResults.setVisible(True)

    @check_for_empty_corpus
    def neighDen(self):
        dialog = NDDialog(self, self.corpusModel,self.showToolTips)
        result = dialog.exec_()
        if result and dialog.results:
            if self.NDWindow is not None and dialog.update and self.NDWindow.isVisible():
                self.NDWindow.table.model().addRows(dialog.results)
            else:
                self.NDWindow = ResultsWindow('Neighborhood density results',dialog,self)
                self.NDWindow.show()
                self.showNDResults.triggered.connect(self.NDWindow.raise_)
                self.showNDResults.triggered.connect(self.NDWindow.activateWindow)
                self.NDWindow.rejected.connect(lambda: self.showNDResults.setVisible(False))
                self.showNDResults.setVisible(True)
        elif result:
            if self.settings['autosave']:
                self.saveCorpus()
                self.saveCorpusAct.setEnabled(False)
            else:
                self.enableSave()

    @check_for_empty_corpus
    @check_for_transcription
    def phonoProb(self):
        dialog = PPDialog(self, self.corpusModel,self.showToolTips)
        result = dialog.exec_()
        if result and dialog.results:
            if self.PPWindow is not None and dialog.update and self.PPWindow.isVisible():
                self.PPWindow.table.model().addRows(dialog.results)
            else:
                self.PPWindow = ResultsWindow('Phonotactic probability results',
                        dialog,self)
                self.PPWindow.show()
                self.showPPResults.triggered.connect(self.PPWindow.raise_)
                self.showPPResults.triggered.connect(self.PPWindow.activateWindow)
                self.PPWindow.rejected.connect(lambda: self.showPPResults.setVisible(False))
                self.showPPResults.setVisible(True)
        elif result:
            if self.settings['autosave']:
                self.saveCorpus()
                self.saveCorpusAct.setEnabled(False)
            else:
                self.enableSave()


    def phonoSearch(self):
        dialog = PhonoSearchDialog(self,self.corpusModel.corpus,self.showToolTips)
        result = dialog.exec_()
        if result:
            if self.PhonoSearchWindow is not None and dialog.update and self.PhonoSearchWindow.isVisible():
                self.PhonoSearchWindow.table.model().addRows(dialog.results)
            else:
                self.PhonoSearchWindow = PhonoSearchResults(
                                'Phonological search results',dialog,self)
                self.PhonoSearchWindow.show()
                self.showSearchResults.triggered.connect(self.PhonoSearchWindow.raise_)
                self.showSearchResults.triggered.connect(self.PhonoSearchWindow.activateWindow)
                self.PhonoSearchWindow.rejected.connect(lambda: self.showSearchResults.setVisible(False))
                self.showSearchResults.setVisible(True)

    def createWord(self):
        dialog = AddWordDialog(self, self.corpusModel.corpus)
        if dialog.exec_():
            self.corpusModel.addWord(dialog.word)
            self.enableSave()

    def toggleWarnings(self):
        self.showWarnings = not self.showWarnings

    def toggleToolTips(self):
        self.showToolTips = not self.showToolTips

    def toggleInventory(self):
        pass

    def toggleText(self):
        if self.showTextAct.isChecked():
            self.textWidget.show()
        else:
            self.textWidget.hide()

    def toggleDiscourses(self):
        if self.showDiscoursesAct.isChecked():
            self.discourseTree.show()
        else:
            self.discourseTree.hide()

    def about(self):
        dialog = AboutDialog(self)
        dialog.exec_()
        #dialog.show()

    def help(self):
        dialog = HelpDialog(self)
        dialog.exec_()

    def checkForUpdates(self):
        if getattr(sys, "frozen", False):
            import esky
            app = esky.Esky(sys.executable,"https://github.com/kchall/CorpusTools/releases")
            try:
                new_version = app.find_update()
                if(new_version != None):
                    reply = QMessageBox.question(self,
                            "Update available", ("Would you like to upgrade "
                                    "from v{} (current) to v{} (latest)?").format(app.active_version,new_version))
                    if reply != QMessageBox.AcceptRole:
                        return None

                    thread = SelfUpdateWorker()
                    thread.setParams({'app':app})

                    progressDialog = QProgressDialog(self)

                    progressDialog.setLabelText('Updating PCT...')
                    progressDialog.setRange(0,0)
                    progressDialog.setWindowTitle('Updating PCT...')
                    thread.updateProgressText.connect(lambda x: progressDialog.setLabelText(x))
                    thread.dataReady.connect(progressDialog.accept)
                    thread.start()
                    result = progressDialog.exec_()
                    if result:
                        appexe = esky.util.appexe_from_executable(sys.executable)
                        os.execv(appexe,[appexe] + sys.argv[1:])
                        app.cleanup()
                        reply = QMessageBox.information(self,
                "Finished updating", "PCT successfully updated to v{}".format(new_version))

                else:

                    reply = QMessageBox.information(self,
                            "Up to date", "The current version ({}) is the latest released.".format(app.active_version))
            except Exception as e:

                reply = QMessageBox.critical(self,
                        "Error encountered", "Something went wrong during the update process.")
            app.cleanup()



    def corpusSummary(self):
        dialog = CorpusSummary(self,self.corpus)
        result = dialog.exec_()

    def createActions(self):

        self.loadCorpusAct = QAction( "L&oad corpus...",
                self, shortcut=QKeySequence.Open,
                statusTip="Load a corpus", triggered=self.loadCorpus)

        self.manageFeatureSystemsAct = QAction( "Manage feature systems...",
                self,
                statusTip="Manage feature systems", triggered=self.loadFeatureMatrices)

        self.createSubsetAct = QAction( "Generate a corpus subset",
                self,
                statusTip="Create and save a subset of the current corpus", triggered=self.subsetCorpus)

        self.saveCorpusAct = QAction( "Save corpus",
                self,
                statusTip="Save corpus", triggered=self.saveCorpus)
        self.saveCorpusAct.setEnabled(False)

        self.exportCorpusAct = QAction( "Export corpus as text file (use with spreadsheets etc.)...",
                self,
                statusTip="Export corpus", triggered=self.exportCorpus)

        self.exportFeatureSystemAct = QAction( "Export feature system as text file...",
                self,
                statusTip="Export feature system", triggered=self.exportFeatureMatrix)

        self.editPreferencesAct = QAction( "Preferences...",
                self,
                statusTip="Edit preferences", triggered=self.showPreferences)

        self.viewFeatureSystemAct = QAction( "View/change feature system...",
                self,
                statusTip="View feature system", triggered=self.showFeatureSystem)

        self.summaryAct = QAction( "Summary",
                self,
                statusTip="Summary of corpus", triggered=self.corpusSummary)

        self.addWordAct = QAction( "Add new word...",
                self,
                statusTip="Add new word", triggered=self.createWord)

        self.addTierAct = QAction( "Add tier...",
                self,
                statusTip="Add tier", triggered=self.createTier)

        self.addAbstractTierAct = QAction( "Add abstract tier...",
                self,
                statusTip="Add abstract tier", triggered=self.createAbstractTier)

        self.addCountColumnAct = QAction( "Add count column...",
                self,
                statusTip="Add count column", triggered=self.createCountColumn)

        self.addColumnAct = QAction( "Add column...",
                self,
                statusTip="Add column", triggered=self.createColumn)

        self.removeAttributeAct = QAction( "Remove tier or column...",
                self,
                statusTip="Remove tier or column", triggered=self.removeAttribute)

        self.phonoSearchAct = QAction( "Phonological search...",
                self,
                statusTip="Search transcriptions", triggered=self.phonoSearch)

        self.neighDenAct = QAction( "Calculate neighborhood density...",
                self,
                statusTip="Calculate neighborhood density", triggered=self.neighDen)

        self.phonoProbAct = QAction( "Calculate phonotactic probability...",
                self,
                statusTip="Calculate phonotactic probability", triggered=self.phonoProb)

        self.stringSimFileAct = QAction( "Calculate string similarity...",
                self,
                statusTip="Calculate string similarity for a file of string pairs")#, triggered=self.stringSim)

        self.stringSimAct = QAction( "Calculate string similarity...",
                self,
                statusTip="Calculate string similarity for corpus", triggered=self.stringSim)

        self.freqaltAct = QAction( "Calculate frequency of alternation...",
                self,
                statusTip="Calculate frequency of alternation", triggered=self.freqOfAlt)

        self.prodAct = QAction( "Calculate predictability of distribution...",
                self,
                statusTip="Calculate predictability of distribution", triggered=self.predOfDist)

        self.funcloadAct = QAction( "Calculate functional load...",
                self,
                statusTip="Calculate functional load", triggered=self.funcLoad)

        self.klAct = QAction( "Calculate Kullback-Leibler...",
                self,
                statusTip="Compare distributions", triggered=self.kullbackLeibler)

        self.mutualInfoAct = QAction( "Calculate mutual information...",
                self,
                statusTip="Calculate mutual information", triggered=self.mutualInfo)

        self.acousticSimFileAct = QAction( "Calculate acoustic similarity (for files)...",
                self,
                statusTip="Calculate acoustic similarity for files", triggered=self.acousticSim)

        self.acousticSimAct = QAction( "Calculate acoustic similarity (from corpus)...",
                self,
                statusTip="Calculate acoustic similarity for corpus")#, triggered=self.acousticSim)

        self.toggleWarningsAct = QAction( "Show warnings",
                self,
                statusTip="Show warnings", triggered=self.toggleWarnings)
        self.toggleWarningsAct.setCheckable(True)
        if self.showWarnings:
            self.toggleWarningsAct.setChecked(True)

        self.toggleToolTipsAct = QAction( "Show tooltips",
                self,
                statusTip="Show tooltips", triggered=self.toggleToolTips)
        self.toggleToolTipsAct.setCheckable(True)
        if self.showToolTips:
            self.toggleToolTipsAct.setChecked(True)

        self.showInventoryAct = QAction( "Show inventory",
                self,
                statusTip="Show inventory", triggered=self.toggleInventory)
        self.showInventoryAct.setCheckable(True)

        self.showTextAct = QAction( "Show corpus text",
                self,
                statusTip="Show text", triggered=self.toggleText)
        self.showTextAct.setCheckable(True)
        self.showTextAct.setEnabled(False)

        self.showDiscoursesAct = QAction( "Show corpus discourses",
                self,
                statusTip="Show discourses", triggered=self.toggleDiscourses)
        self.showDiscoursesAct.setCheckable(True)
        self.showDiscoursesAct.setEnabled(False)

        self.quitAct = QAction("&Quit", self, shortcut="Ctrl+Q",
                statusTip="Quit the application", triggered=self.close)

        self.aboutAct = QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

        self.helpAct = QAction("&Help", self,
                statusTip="Help information",
                triggered=self.help)

        self.updateAct = QAction("Check for updates...", self,
                statusTip="Check for updates",
                triggered=self.checkForUpdates)

        self.showSearchResults = QAction("Phonological search results", self)
        self.showSearchResults.setVisible(False)

        self.showSSResults = QAction("String similarity results", self)
        self.showSSResults.setVisible(False)

        self.showMIResults = QAction("Mutual information results", self)
        self.showMIResults.setVisible(False)

        self.showASResults = QAction("Acoustic similarity results", self)
        self.showASResults.setVisible(False)

        self.showFLResults = QAction("Functional load results", self)
        self.showFLResults.setVisible(False)

        self.showKLResults = QAction("Kullback-Leibler results", self)
        self.showKLResults.setVisible(False)

        self.showFAResults = QAction("Frequency of alternation results", self)
        self.showFAResults.setVisible(False)

        self.showPDResults = QAction("Predictability of distribution results", self)
        self.showPDResults.setVisible(False)

        self.showNDResults = QAction("Neighborhood density results", self)
        self.showNDResults.setVisible(False)

        self.showPPResults = QAction("Phonotactic probability results", self)
        self.showPPResults.setVisible(False)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.loadCorpusAct)
        self.fileMenu.addAction(self.manageFeatureSystemsAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.createSubsetAct)
        self.fileMenu.addAction(self.saveCorpusAct)
        self.fileMenu.addAction(self.exportCorpusAct)
        self.fileMenu.addAction(self.exportFeatureSystemAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.quitAct)

        self.editMenu = self.menuBar().addMenu("&Options")
        self.editMenu.addAction(self.editPreferencesAct)
        self.editMenu.addAction(self.toggleWarningsAct)
        self.editMenu.addAction(self.toggleToolTipsAct)

        self.corpusMenu = self.menuBar().addMenu("&Corpus")
        self.corpusMenu.addAction(self.summaryAct)
        self.corpusMenu.addSeparator()
        self.corpusMenu.addAction(self.addWordAct)
        self.corpusMenu.addSeparator()
        self.corpusMenu.addAction(self.addTierAct)
        self.corpusMenu.addAction(self.addAbstractTierAct)
        self.corpusMenu.addAction(self.addCountColumnAct)
        self.corpusMenu.addAction(self.addColumnAct)
        self.corpusMenu.addSeparator()
        self.corpusMenu.addAction(self.removeAttributeAct)
        self.corpusMenu.addSeparator()
        self.corpusMenu.addAction(self.phonoSearchAct)

        self.featureMenu = self.menuBar().addMenu("&Features")
        self.featureMenu.addAction(self.viewFeatureSystemAct)

        self.analysisMenu = self.menuBar().addMenu("&Analysis")
        self.analysisMenu.addAction(self.phonoProbAct)
        self.analysisMenu.addAction(self.funcloadAct)
        self.analysisMenu.addAction(self.prodAct)
        self.analysisMenu.addAction(self.klAct)
        self.analysisMenu.addAction(self.stringSimAct)
        self.analysisMenu.addAction(self.neighDenAct)
        self.analysisMenu.addAction(self.freqaltAct)
        self.analysisMenu.addAction(self.mutualInfoAct)
        self.analysisMenu.addAction(self.acousticSimFileAct)

        #self.otherMenu = self.menuBar().addMenu("Other a&nalysis")

        self.viewMenu = self.menuBar().addMenu("&Windows")
        #self.viewMenu.addAction(self.showInventoryAct)
        self.viewMenu.addAction(self.showDiscoursesAct)
        self.viewMenu.addAction(self.showTextAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.showPPResults)
        self.viewMenu.addAction(self.showFLResults)
        self.viewMenu.addAction(self.showPDResults)
        self.viewMenu.addAction(self.showKLResults)
        self.viewMenu.addAction(self.showSSResults)
        self.viewMenu.addAction(self.showNDResults)
        self.viewMenu.addAction(self.showFAResults)
        self.viewMenu.addAction(self.showMIResults)
        self.viewMenu.addAction(self.showASResults)
        self.viewMenu.addAction(self.showSearchResults)

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.updateAct)
        self.helpMenu.addSeparator()
        self.helpMenu.addAction(self.helpAct)
        self.helpMenu.addAction(self.aboutAct)

    #@check_for_unsaved_changes
    #def close(self):
    #    QMainWindow.close(self)

    def closeEvent(self, event):

        if self.unsavedChanges:
            reply = QMessageBox()
            reply.setWindowTitle("Unsaved changes")
            reply.setIcon(QMessageBox.Warning)
            reply.setText("The currently loaded corpus ('{}') has unsaved changes.".format(self.corpus.name))
            reply.setInformativeText("Do you want to save your changes?")

            reply.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            reply.setDefaultButton(QMessageBox.Save)
            ret = reply.exec_()
            if ret == QMessageBox.Save:
                self.saveCorpus()
            elif ret == QMessageBox.Cancel:
                event.ignore()
                return
        self.corpusModel = None
        if self.FLWindow is not None:
            self.FLWindow.reject()
            #self.FLWindow.deleteLater()
        if self.PDWindow is not None:
            self.PDWindow.reject()
            #self.PDWindow.deleteLater()
        if self.FAWindow is not None:
            self.FAWindow.reject()
            #self.FAWindow.deleteLater()
        if self.SSWindow is not None:
            self.SSWindow.reject()
            #self.SSWindow.deleteLater()
        if self.ASWindow is not None:
            self.ASWindow.reject()
            #self.ASWindow.deleteLater()
        if self.NDWindow is not None:
            self.NDWindow.reject()
            #self.NDWindow.deleteLater()
        if self.PPWindow is not None:
            self.PPWindow.reject()
            #self.PPWindow.deleteLater()
        if self.MIWindow is not None:
            self.MIWindow.reject()
            #self.MIWindow.deleteLater()
        if self.KLWindow is not None:
            self.KLWindow.reject()
            #self.KLWindow.deleteLater()
        if self.PhonoSearchWindow is not None:
            self.PhonoSearchWindow.reject()
            #self.PhonoSearchWindow.deleteLater()
        self.settings['size'] = self.size()
        self.settings['pos'] = self.pos()
        #tmpfiles = os.listdir(TMP_DIR)
        #for f in tmpfiles:
        #    os.remove(os.path.join(TMP_DIR,f))
        super(MainWindow, self).closeEvent(event)

    def cleanUp(self):
        # Clean up everything
        for i in self.__dict__:
            item = self.__dict__[i]
            clean(item)
     # end cleanUp
# end class CustomWindow

def clean(item):
    """Clean up the memory by closing and deleting the item if possible."""
    if isinstance(item, list) or isinstance(item, dict):
        for _ in range(len(item)):
            clean(item.pop())
    else:
        try:
            item.close()
        except (RuntimeError, AttributeError): # deleted or no close method
            pass
        try:
            item.deleteLater()
        except (RuntimeError, AttributeError): # deleted or no deleteLater method
            pass
# end cleanUp
