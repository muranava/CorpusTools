#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      JSMIII
#
# Created:     08/01/2014
# Copyright:   (c) JSMIII 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

from tkinter import *
from tkinter.ttk import *
from tkinter import Radiobutton as OldRadiobutton
#ttk.Radiobutton doesn't support the indicatoron option, which is used for some
#of the windows
import tkinter.messagebox as MessageBox
import tkinter.filedialog as FileDialog
import corpustools
import threading
import queue
import pickle
import os
import string
import MRel as string_sim
import collections
from codecs import open
from math import log

class ThreadedTask(threading.Thread):
    def __init__(self, queue, **kwargs):
        threading.Thread.__init__(self,target=kwargs['target'], args=kwargs['args'])
        self.queue = queue

class MultiListbox(Frame):
    def __init__(self, master, lists):
        Frame.__init__(self, master)
        self.lists = []
        self.headers = [l for l,w in lists]
        for l,w in lists:
            frame = Frame(self); frame.pack(side=LEFT, expand=YES, fill=BOTH)
            Label(frame, text=l, borderwidth=1, relief=RAISED).pack(fill=X)
            lb = Listbox(frame, width=w, borderwidth=0, selectborderwidth=0,relief=FLAT, exportselection=FALSE)
            lb.pack(expand=YES, fill=BOTH)
            self.lists.append(lb)
            lb.bind('<B1-Motion>', lambda e, s=self: s._select(e.y))
            lb.bind('<Button-1>', lambda e, s=self: s._select(e.y))
            lb.bind('<Leave>', lambda e: 'break')
            lb.bind('<B2-Motion>', lambda e, s=self: s._b2motion(e.x, e.y))
            lb.bind('<Button-2>', lambda e, s=self: s._button2(e.x, e.y))
        frame = Frame(self); frame.pack(side=LEFT, fill=Y)
        Label(frame, borderwidth=1, relief=RAISED).pack(fill=X)
        sb = Scrollbar(frame, orient=VERTICAL, command=self._scroll)
        sb.pack(expand=YES, fill=Y)
        self.lists[0]['yscrollcommand']=sb.set


    def _select(self, y):
        row = self.lists[0].nearest(y)
        self.selection_clear(0, END)
        self.selection_set(row)
        return 'break'

    def _button2(self, x, y):
        for l in self.lists:
            l.scan_mark(x, y)
        return 'break'

    def _b2motion(self, x, y):
        for l in self.lists:
            l.scan_dragto(x, y)
        return 'break'

    def _scroll(self, *args):
        for l in self.lists:
            l.yview(*args)

    def curselection(self):
        return self.lists[0].curselection()

    def delete(self, first, last=None):
        for l in self.lists:
            l.delete(first, last)

    def get(self, first, last=None):
        result = []
        for l in self.lists:
            result.append(l.get(first,last))
        if last:
            return map(None, *result)
        return result

    def index(self, index):
        self.lists[0].index(index)

    def insert(self, index, *elements):
        for e in elements:
            i = 0
            for l in self.lists:
                l.insert(index, e[i])
                i = i + 1

    def size(self):
        return self.lists[0].size()

    def see(self, index):
        for l in self.lists:
            l.see(index)

    def selection_anchor(self, index):
        for l in self.lists:
            l.selection_anchor(index)

    def selection_clear(self, first, last=None):
        for l in self.lists:
            l.selection_clear(first, last)

    def selection_includes(self, index):
        return self.lists[0].selection_includes(index)

    def selection_set(self, first, last=None):
        for l in self.lists:
            l.selection_set(first, last)


class GUI(Toplevel):

    def __init__(self,master):
        self.master = master
        self.show_warnings = False
        self.q = queue.Queue()
        self.corpusq = queue.Queue(1)
        self.corpus = None
        self.feature_system = None
        self.all_feature_systems = ['spe','hayes']
        self.corpus_factory = corpustools.CorpusFactory()

        #TKINTER VARIABLES ("globals")
        #main screen variabls
        self.corpus_report_label_var = StringVar()
        self.corpus_report_label_var.set('0 words loaded from corpus')
        self.corpus_button_var = StringVar()
        self.features_button_var = StringVar()
        self.search_var = StringVar()
        #string similarity variables
        self.string_sim_query_var = StringVar()
        self.string_sim_filename_var = StringVar()
        self.string_sim_typetoken_var = StringVar()
        self.string_sim_stringtype_var = StringVar()
        #corpus information variables
        self.feature_system_var = StringVar()
        self.feature_system_var.set('No feature system selected')
        self.recently_selected_system = 'spe'
        self.corpus_var = StringVar()
        self.corpus_var.set('No corpus selected')
        self.corpus_size_var = IntVar()
        self.corpus_size_var.set(0)
        #entropy calculation variables
        self.entropy_tier_var = StringVar()
        self.entropy_typetoken_var = StringVar()
        self.letter1_var = StringVar()
        self.letter2_var = StringVar()
        self.seg1_var = StringVar()
        self.seg2_var = StringVar()
        self.lhs_feature_var = StringVar()
        self.rhs_feature_var = StringVar()
        self.lhs_seg_var = StringVar()
        self.rhs_seg_var = StringVar()
        self.entropy_filename_var = StringVar()
        self.entropy_exhaustive_var = IntVar()
        self.entropy_uniqueness_var = IntVar()
        self.entropy_exclusive_var = IntVar()
        #Corpus from text variables
        self.punc_vars = [IntVar() for mark in string.punctuation]
        self.new_corpus_string_type = StringVar()
        self.new_corpus_feature_system_var = StringVar()

        #
        self.main_screen = Frame(master)
        self.main_screen.grid()
        self.info_frame = Frame(self.main_screen)
        self.info_frame.grid()

        self.check_for_feature_systems()
        corpus_info_label = Label(self.info_frame ,text='Corpus: No corpus selected')#textvariable=self.corpus_var)
        corpus_info_label.grid()
        size_info_label = Label(self.info_frame, text='Size: No corpus selected')#textvariable=self.corpus_size_var)
        size_info_label.grid()
        feature_info_label = Label(self.info_frame, text='Feature system: No features selected', )#textvariable=self.feature_system_var)
        feature_info_label.grid()
        self.corpus_frame = Frame(self.main_screen)
        self.corpus_frame.grid()

    def check_for_feature_systems(self):
        ignore = ['cmu2ipa.txt', 'cmudict.txt', 'ipa2hayes.txt', 'ipa2spe.txt']
        for dirpath,dirname,filenames in os.walk(os.path.join(os.getcwd(),'TRANS')):
            for name in filenames:
                if name in ignore:
                    continue
                system_name = name.split('.')[0]
                self.all_feature_systems.append(system_name)


    def quit(self,event=None):
        root.quit()

    def populate_inventory(self):
        """
        Put the inventory on screen, making each segment a button that pops up
        a window to view more detailed segmental information
        """

        cons_chart = ConsChart()
        vowel_chart = VowelChart()
        for seg,features in self.current_inventory.items():
            if '-voc' in self.current_inventory[seg]:
                cons_chart.match_to_chart(seg,features)
            else:
                vowel_chart.match_to_chart(seg,features)
        self.inventory_bigframe.configure(text='Inventory ({})'.format(len(cons_chart.inventory)))
        row = 1
        col = 2
        for cname in cons_chart.col_names:
            col_label = Label(self.Cinventory_frame, text=cname[0])
            col_label.grid(row=1, column=col)
            col += 1

        for vname in vowel_chart.col_names:
            col_label = Label(self.Vinventory_frame, text=vname[0])
            col_label.grid(row=1, column=col)
            col += 1

        for rname in cons_chart.row_names:
            row += 1
            col = 1
            row_label = Label(self.Cinventory_frame, text=rname[0])
            row_label.grid(row=row, column=col)
            for cname in cons_chart.col_names:
                col += 1
                seg_box = Frame(self.Cinventory_frame, borderwidth=5, width=10)
                seg_box.grid(row=row,column=col)
                for seg,voiced in cons_chart.display_matrix[rname[0]][cname[0]]:
                    if voiced:
                        colour = 'gold'
                    else:
                        colour = 'white smoke'
                    seg_button = Button(seg_box, text=seg, command=lambda symbol=seg: self.show_segment_info(symbol))
                    seg_button.config(bg=colour)
                    seg_button.grid()

        for rname in vowel_chart.row_names:
            row += 1
            col = 1
            row_label = Label(self.Vinventory_frame, text=rname[0])
            row_label.grid(row=row, column=col)
            for cname in vowel_chart.col_names:
                col += 1
                seg_box = Frame(self.Vinventory_frame)
                seg_box.grid(row=row,column=col)
                for seg,rounded in vowel_chart.display_matrix[rname[0]][cname[0]]:
                    if rounded:
                        colour = 'gold'
                    else:
                        colour = 'white smoke'
                    seg_button = Button(seg_box, text=seg, command=lambda symbol=seg: self.show_segment_info(symbol))
                    seg_button.config(bg=colour)
                    seg_button.grid()


    def update_info_frame(self):
        for child in self.info_frame.winfo_children():
            child.destroy()

        corpus_info_label = Label(self.info_frame ,text='Corpus: {}'.format(self.corpus.name))#textvariable=self.corpus_var)
        corpus_info_label.grid()

        size_info_label = Label(self.info_frame, text='Size: {}'.format(len(self.corpus)))#textvariable=self.corpus_size_var)
        size_info_label.grid()

        feature_info_label = Label(self.info_frame, text='Feature system: {}'.format(self.feature_system) )#textvariable=self.feature_system_var)
        feature_info_label.grid()

    def navigate_to_corpus_file(self):
        custom_corpus_filename = FileDialog.askopenfilename(filetypes=(('Text files', '*.txt'),('Corpus files', '*.corpus')))
        if custom_corpus_filename:
            self.custom_corpus_path.delete(0,END)
            self.custom_corpus_path.insert(0, custom_corpus_filename)
            self.custom_corpus_name.delete(0,END)
            suggestion = os.path.basename(custom_corpus_filename).split('.')[0]
            self.custom_corpus_name.insert(0,suggestion)

    def choose_custom_corpus(self, event=None):

        self.custom_corpus_load_screen = Toplevel()
        self.custom_corpus_load_screen.title('Load custom corpus')
        custom_corpus_load_frame = LabelFrame(self.custom_corpus_load_screen, text='Corpus information')
        custom_corpus_load_frame.grid()
        corpus_path_label = Label(custom_corpus_load_frame, text='Path to corpus')
        corpus_path_label.grid()
        self.custom_corpus_path = Entry(custom_corpus_load_frame)
        self.custom_corpus_path.grid()
        select_corpus_button = Button(custom_corpus_load_frame, text='Choose file...', command=self.navigate_to_corpus_file)
        select_corpus_button.grid()
        corpus_name_label = Label(custom_corpus_load_frame, text='Name for corpus (auto-suggested)')
        corpus_name_label.grid()
        self.custom_corpus_name = Entry(custom_corpus_load_frame)
        self.custom_corpus_name.grid()
        delimiter_label = Label(custom_corpus_load_frame, text='Delimiter (enter \'t\' for tab)')
        delimiter_label.grid()
        self.delimter_entry = Entry(custom_corpus_load_frame)
        self.delimter_entry.insert(0,',')
        self.delimter_entry.grid()
        new_corpus_feature_frame = LabelFrame(custom_corpus_load_frame, text='Feature system to use (if transcription exists)')
        new_corpus_feature_system = OptionMenu(new_corpus_feature_frame,#parent
            self.new_corpus_feature_system_var,#variable
            'spe',#selected option,
            *[fs for fs in self.all_feature_systems])#options in drop-down
        new_corpus_feature_system.grid()
        new_corpus_feature_frame.grid(sticky=W)
        ok_button = Button(self.custom_corpus_load_screen, text='OK', command=self.confirm_custom_corpus_selection)
        cancel_button = Button(self.custom_corpus_load_screen, text='Cancel', command=self.custom_corpus_load_screen.destroy)
        ok_button.grid()
        cancel_button.grid()


    def confirm_custom_corpus_selection(self):
        filename = self.custom_corpus_path.get()
        if not os.path.exists(filename):
            MessageBox.showerror(message='Corpus file could not be located. Please verify the path and file name.')

        delimiter = self.delimter_entry.get()
        corpus_name = self.custom_corpus_name.get()
        if (not filename) or (not delimiter) or (not corpus_name):
            MessageBox.showerror(message='Information is missing. Please verify that you entered something in all the text boxes')
            return
        if delimiter == 't':
            delimiter = '\t'
        self.create_custom_corpus(corpus_name, filename, delimiter)

    def custom_corpus_worker_thread(self, corpus_name, filename, delimiter, queue, corpusq):
        with open(filename, encoding='utf-8') as f:
            headers = f.readline()
            headers = headers.split(delimiter)
            if len(headers)==1:
                #delimiter is incorrect
                MessageBox.showerror(message='Could not parse the corpus.\nCheck that the delimiter you typed in matches the one used in the file.')
                return

            #headers = [h.strip().lower() for h in headers]
            headers = [h.strip() for h in headers]
            headers[0] = headers[0].strip('\ufeff')
            if 'feature_system' in headers[-1]:
                feature_system = headers[-1].split('=')[1]
                headers = headers[0:len(headers)-1]
                #headers = [h.lower() for h in headers]
            elif self.new_corpus_feature_system_var.get():
                feature_system = self.new_corpus_feature_system_var.get()
            else:
                feature_system = 'spe'#default

            corpus = corpustools.Corpus(corpus_name)
            self.corpus_factory.specifier = corpustools.FeatureSpecifier(encoding=feature_system)
            segs_list = list(self.corpus_factory.specifier.matrix.keys())
            transcription_errors = collections.defaultdict(list)
            for line in f:
                line = line.strip()
                if not line: #blank or just a newline
                    continue
                d = {attribute:value.strip() for attribute,value in zip(headers,line.split(delimiter))}
                word = corpustools.Word(**d)
                if word.transcription:
                    #transcriptions can have phonetic symbol delimiters which is a period
                    word.transcription = word.transcription.split('.')
                    if len(word.transcription) == 1: #the split didn't work, there's no delimiters
                        word.transcription = list(word.transcription[0])
                    if not word.spelling:
                        word.spelling = ''.join(word.transcription)
                    try:
                        word._specify_features(self.corpus_factory)
                        word.set_string('transcription')
                    except KeyError as e:
                        transcription_errors[str(e)].append(str(word))
                        continue

                corpus.add_word(word)
                queue.put(1)
        queue.put(-99)#flag
        corpus.orthography.extend([letter for letter in word.spelling if not letter in corpus.orthography])
        corpus.inventory.extend([seg for seg in word.transcription if not seg in corpus.inventory])
        corpus.orthography.append('#')
        corpus.inventory.append(corpustools.Segment('#'))
        corpus.specifier = corpustools.FeatureSpecifier(encoding=feature_system)
        corpus.custom = True
        corpusq.put(transcription_errors)
        corpusq.put(corpus)

    def create_custom_corpus(self, corpus_name, filename, delimiter):

        try:
            with open(filename, 'rb') as f:
                corpus = pickle.load(f)
            corpus.custom = True
            self.finalize_corpus(corpus)
            return
        except (pickle.UnpicklingError, ValueError):
            pass

        self.q = queue.Queue()
        self.custom_corpus_load_prog_bar = Progressbar(self.custom_corpus_load_screen, mode='indeterminate')
        #this progbar is indeterminate because we can't know how big the custom corpus will be
        self.custom_corpus_load_prog_bar.grid()
        self.custom_corpus_load_thread = ThreadedTask(self.q,
                                target=self.custom_corpus_worker_thread,
                                args=(corpus_name, filename, delimiter, self.q, self.corpusq))
        self.custom_corpus_load_thread.start()
        self.process_custom_corpus_queue()

    def finalize_corpus(self, corpus, transcription_errors=None):
        self.corpus = corpus
        self.feature_system = corpus.specifier.feature_system
        try:
            self.custom_corpus_load_screen.destroy()
        except AttributeError:
            pass #this occurs if the custom corpus was created from text, not loaded directly

        if transcription_errors:
            filename = 'error_{}_{}.txt'.format(self.new_corpus_feature_system_var.get(), self.corpus.name)
            with open(os.path.join(os.getcwd(),'ERRORS',filename), encoding='utf-8', mode='w') as f:
                print('Some words in your corpus contain symbols that have no match in the \'{}\' feature system you\'ve selected.\r\n'.format(self.new_corpus_feature_system_var.get()),file=f)
                print('To fix this problem, open the features file in a text editor and add the missing symbols and appropriate feature specifications\r\n', file=f)
                print('All feature files are (or should be!) located in the TRANS folder. If you have your own feature file, just drop it into that folder before loading CorpusTools.\r\n', file=f)
                print('The following segments could not be represented:\r\n',file=f)
                for key in sorted(list(transcription_errors.keys())):
                    words = sorted(transcription_errors[key])
                    words = ','.join(words)
                    sep = '\r\n\n'
                    print('Symbol: {}\r\nWords: {}\r\n{}'.format(key,words,sep), file=f)
            msg1 = 'Not every symbol in your corpus can be interpreted with this feature system.'
            msg2 = 'A file called {} has been placed in your ERRORS folder explaining this problem in more detail.'.format(
            filename)
            msg3 = 'Words with interpretable symbols will still be displayed. Consult the output file above to see how to fix this problem.'
            msg = '\n'.join([msg1, msg2, msg3])
            MessageBox.showwarning(message=msg)


        self.main_screen_refresh()


    def search(self):
        if self.feature_system is None:
            MessageBox.showerror(message='No corpus selected')
            return

        self.search_popup = Toplevel()
        self.search_popup.title('Search {}'.format(self.corpus.name))
        search_frame = LabelFrame(self.search_popup, text='Enter search term')
        search_entry = Entry(search_frame, textvariable=self.search_var)
        search_entry.grid()
        search_frame.grid()
        ok_button = Button(self.search_popup, text='OK', command=self._search)
        cancel_button = Button(self.search_popup, text='Cancel', command=self.search_popup.destroy)
        ok_button.grid()
        cancel_button.grid()

    def _search(self):
        query = self.search_var.get()
        query = query.lower()
        try:
            self.corpus.find(query, keyerror=True)
        except KeyError:
            MessageBox.showerror(message='The word \"{}\" is not in the corpus'.format(query))
            return
        self.corpus_box.selection_clear(0,END)
        for i in range(len(self.corpus)):
            word = self.corpus_box.get(i)
            word = word[0].lower()
            try:
                word,n = word.split('(')
            except ValueError:
                pass
            if word == query:
                self.corpus_box.selection_set(i)
                self.corpus_box.see(i)
                break
        self.search_popup.destroy()


    def string_similarity(self):

        #Check if it's even possible to do this analysis
        has_spelling = True
        has_transcription = True
        has_frequency = True
        missing = list()
        if self.corpus.custom:
            random_word = self.corpus.random_word()
            if not 'spelling' in random_word.descriptors:# or not random_word.spelling:
                has_spelling = False
                missing.append('spelling')
            if not 'transcription' in random_word.descriptors:# or not random_word.transcription:
                has_transcription = False
                missing.append('transcription')
            if not 'frequency' in random_word.descriptors:# or not random_word.frequency:
                has_frequency = False
                missing.append('token frequency')

            if self.show_warnings and not (has_spelling and has_transcription and has_frequency):
                missing = ','.join(missing)
                MessageBox.showwarning(message='Some information neccessary for this analysis is missing from your corpus: {}\nYou will not be able to select every option'.format(missing))

        self.string_sim_popup = Toplevel()
        self.string_sim_popup.title('String similarity')
        try:
            selection = self.corpus_box.get(self.corpus_box.curselection())[0]
        except TclError:
            #this means that nothing was selected in the multibox
            selection = ''

        word1_frame = LabelFrame(self.string_sim_popup, text='Enter a word')
        word1_frame.grid()
        word1_entry = Entry(word1_frame, textvariable=self.string_sim_query_var)
        word1_entry.delete(0,END)
        word1_entry.insert(0,selection)
        word1_entry.grid()

        filename_frame = LabelFrame(self.string_sim_popup, text='Name for output file')
        string_sim_filename_entry = Entry(filename_frame, textvariable=self.string_sim_filename_var)
        string_sim_filename_entry.delete(0,END)
        if selection:
            string_sim_filename_entry.insert(0,'{}_string_similarity.txt'.format(selection))
        string_sim_filename_entry.grid()
        filename_frame.grid()

        options_frame = LabelFrame(self.string_sim_popup, text='Options')
        typetoken_frame = LabelFrame(options_frame, text='Type or Token')
        type_button = Radiobutton(typetoken_frame, text='Count types', variable=self.string_sim_typetoken_var, value='type')
        type_button.grid(sticky=W)
        type_button.invoke()
        token_button = Radiobutton(typetoken_frame, text='Count tokens', variable=self.string_sim_typetoken_var, value='token')
        token_button.grid(sticky=W)
        if not has_frequency:
            token_button.configure(state=('disabled'))
        typetoken_frame.grid(column=0, row=0)
        stringtype_frame = LabelFrame(options_frame, text='String type')
        spelling_button = Radiobutton(stringtype_frame, text='Compare spelling', variable=self.string_sim_stringtype_var, value='spelling')
        spelling_button.grid(sticky=W)
        spelling_button.invoke()
        if not has_spelling:
            transcription_button.configure(state=('disabled'))
        transcription_button = Radiobutton(stringtype_frame, text='Compare transcription', variable=self.string_sim_stringtype_var, value='transcription')
        transcription_button.grid(sticky=W)
        if not has_transcription:
            transcription_button.configure(state=('disabled'))
        stringtype_frame.grid(column=1, row=0)
        options_frame.grid()

        ok_button = Button(self.string_sim_popup, text='OK', command=self.calculate_string_sim)
        ok_button.grid()
        if not has_spelling and has_transcription:
            ok_button.state = DISABLED
        cancel_button = Button(self.string_sim_popup, text='Cancel', command=self.cancel_string_similarity)
        cancel_button.grid()
        info_button = Button(self.string_sim_popup, text='About this function...', command=self.string_sim_info)
        info_button.grid()

    def string_sim_info(self):

        info_popup = Toplevel()
        description_frame = LabelFrame(info_popup, text='Brief description')
        text = 'This function calculates substring similarity, and can be used as a proxy for morphological relatedness'
        description_label = Label(description_frame, text=text)
        description_label.grid()
        description_frame.grid(sticky=W)
        citation_frame = LabelFrame(info_popup, text='Original source')
        citation_label = Label(citation_frame, text='Khorsi, A. 2012. On Morphological Relatedness. Natural Language Engineering, 1-19.')
        citation_label.grid()
        citation_frame.grid(sticky=W)
        author_frame = LabelFrame(info_popup, text='Coded by')
        author_label = Label(author_frame, text='Micheal Fry')
        author_label.grid()
        author_frame.grid(sticky=W)

    def entropy_info(self):

        info_popup = Toplevel()
        description_frame = LabelFrame(info_popup, text='Brief description')
        description_label = Label(description_frame, text='This function calculates the entropy of two segments')
        description_label.grid()
        description_frame.grid(sticky=W)
        citation_frame = LabelFrame(info_popup, text='Original source')
        citation_label = Label(citation_frame, text='Hall, K.C. 2009. A probabilistic model of phonological relationships from contrast to allophony. PhD dissertation, The Ohio State University.')
        citation_label.grid()
        citation_frame.grid(sticky=W)
        author_frame = LabelFrame(info_popup, text='Coded by')
        author_label = Label(author_frame, text='Scott Mackie, Blake Allen')
        author_label.grid()
        author_frame.grid(sticky=W)

    def calculate_string_sim(self):

        #First check if the word is in the corpus
        query = self.string_sim_query_var.get()
        try:
            self.corpus.find(query,keyerror=True)
        except KeyError:
            message = 'The word \"{}\" is not in the corpus'.format(query)
            MessageBox.showerror(message=message)
            return

        #Then check for a filename
        filename = self.string_sim_filename_var.get()
        if not filename:
            MessageBox.showerror(message='Please enter a filename')
            return
        if not filename.endswith('.txt'):
            filename += '.txt'

        #If it's all good, then calculate relatedness
        relator = string_sim.Relator(ready_made_corpus=self.corpus)
        relator.relate(query, filename,
                        count_what=self.string_sim_typetoken_var.get(),
                        string_type=self.string_sim_stringtype_var.get())
        string_type = self.string_sim_stringtype_var.get()
        string_type = string_type[0].upper()+string_type[1:]
        string_sim_results_popup = Toplevel()
        title = 'Counting {}, Comparing {}'.format(self.string_sim_typetoken_var.get(),
                                                 self.string_sim_stringtype_var.get())
        string_sim_results_popup.title(title)
        string_sim_results_frame = LabelFrame(string_sim_results_popup, text='Results')
        string_sim_results_box = MultiListbox(string_sim_results_popup,
                    [('Relatedness to \"{}\"'.format(self.string_sim_query_var.get()),20),
                    (string_type, 10)])

        #Read from results file and display in a multibox
        with open(os.path.join(os.getcwd(),filename), encoding='utf-8') as f:
            for line in f:
                try:
                    score, spelling = line.split(']')
                except ValueError:
                    continue
                score = score[1:]
                spelling = spelling.strip()
                string_sim_results_box.insert(END,[score, spelling])
        string_sim_results_box.grid()
        string_sim_results_frame.grid()

    def cancel_string_similarity(self):
        self.string_sim_popup.destroy()

    def donothing(self,event=None):
        pass

    def suggest_filename(self):
        seg1 = self.seg1_var.get()
        seg2 = self.seg2_var.get()
        if not seg1 or not seg2:
            MessageBox.showwarning(message='Select 2 segments first!')
            return
        filename = 'entropy_of_{}_{}_{}.txt'.format(seg1, seg2, self.entropy_typetoken_var.get())
        self.entropy_output_file_entry.delete(0,END)
        self.entropy_output_file_entry.insert(0,filename)

    def save_corpus_as(self):
        """
        pickles the corpus, makes loading it WAY easier
        would be nice to have an option to save as pickle, or maybe "export as"
        a .txt/csv file
        """
        filename = FileDialog.asksaveasfilename(filetypes=(('Corpus file', '*.corpus'),))
        if not filename:
            return

        if not filename.endswith('.corpus'):
            filename += '.corpus'
        with open(filename, 'wb') as f:
            self.corpus.feature_system = self.feature_system
            pickle.dump(self.corpus, f)

    def choose_corpus(self,event=None):
        #This is always called from a menu
        self.corpus_select_screen = Toplevel()
        self.corpus_select_screen.title('Corpus select')

        corpus_area = LabelFrame(self.corpus_select_screen, text='Select a corpus')
        corpus_area.grid(sticky=W, column=0, row=0)
        subtlex_button = Radiobutton(corpus_area, text='SUBTLEX', variable=self.corpus_button_var, value='subtlex')
        subtlex_button.grid(sticky=W,row=0)
        subtlex_button.invoke()#.select() doesn't work on ttk.Button
        iphod_button = Radiobutton(corpus_area, text='IPHOD', variable=self.corpus_button_var, value='iphod')
        iphod_button.grid(sticky=W,row=1)

        features_area = LabelFrame(self.corpus_select_screen, text='Select a feature system')
        features_area.grid(sticky=E, column=1, row=0)
        spe_button = Radiobutton(features_area, text='Sound Pattern of English (Chomsky and Halle, 1967)', variable=self.features_button_var, value='spe')
        spe_button.grid(sticky=W, row=0)
        spe_button.invoke()#.select() doesn't work on ttk.Button
        hayes_button = Radiobutton(features_area, text='Hayes (2008)', variable=self.features_button_var, value='hayes')
        hayes_button.grid(sticky=W, row=1)

        ok_button = Button(self.corpus_select_screen,text='OK', command=self.confirm_corpus_selection)
        ok_button.grid(row=3, column=0)#, sticky=W, padx=3)
        cancel_button = Button(self.corpus_select_screen,text='Cancel', command=self.corpus_select_screen.destroy)
        cancel_button.grid(row = 3, column=1)#, sticky=W, padx=3)

    def confirm_corpus_selection(self):
        corpus_name = self.corpus_button_var.get()
        features_name = self.features_button_var.get()
        self.feature_system = features_name
        self.load_corpus(corpus_name, features_name)

    def process_queue(self):
        try:
            msg = self.q.get(0)
            if msg == 'done':
                self.corpus_load_prog_bar.stop()
                #self.corpus_load_prog_bar.destroy()
                self.corpus_select_screen.destroy()
                self.corpus = self.corpusq.get()
                self.main_screen_refresh()
                return
            else:
                self.corpus_load_prog_bar.step()
                #self.master.after(100, self.process_queue)
                self.corpus_select_screen.after(3, self.process_queue)
        except queue.Empty:
            #queue is empty initially for a while because it takes some time for the
            #corpus_factory.make_corpus to actually start producing worsd
            self.corpus_select_screen.after(10, self.process_queue)

    def process_custom_corpus_queue(self):
        try:
            msg = self.q.get(0)
            if msg == -99:
                self.custom_corpus_load_prog_bar.stop()
                #self.corpus_load_prog_bar.destroy()
                self.custom_corpus_load_screen.destroy()
                transcription_errors = self.corpusq.get()
                corpus = self.corpusq.get()
                self.finalize_corpus(corpus, transcription_errors)
                return
            else:
                self.custom_corpus_load_prog_bar.step()
                #self.master.after(100, self.process_queue)
                self.custom_corpus_load_screen.after(3, self.process_custom_corpus_queue)
        except queue.Empty:
            #queue is empty initially for a while because it takes some time for the
            #corpus_factory.make_corpus to actually start producing worsd
            self.custom_corpus_load_screen.after(10, self.process_custom_corpus_queue)

    def load_corpus(self, corpus_name, features_name, size=5000):
        """
        good if size is fixed low for testing purposes, the actual program would probably want
        to load the entire corpus every time
        """
        #pre-computed size variables
        if size == 'all':
            if corpus_name == 'iphod':
                size = 54030
            elif corpus_name == 'subtlex':
                size = 48212
        self.q = queue.Queue()
        self.corpus_load_prog_bar = Progressbar(self.corpus_select_screen, mode='determinate', maximum=size)
        self.corpus_load_prog_bar.grid()
        #self.corpus_load_prog_bar.start()
        self.corpus_load_thread = ThreadedTask(self.q,
                                target=self.corpus_factory.make_corpus_from_gui,
                                args=(corpus_name, features_name, size, self.q, self.corpusq))
        self.corpus_load_thread.start()
        self.process_queue()

    def main_screen_refresh(self):

        for child in self.corpus_frame.winfo_children():
            child.grid_forget()

        random_word = self.corpus.random_word()
        headers = [d for d in random_word.descriptors if not d is None or not d == '']
        self.corpus_box = MultiListbox(self.corpus_frame, [(h,10) for h in headers])
        self.update_info_frame()
        for word in self.corpus.iter_sort():
            #corpus.iter_sort is a generator that sorts the corpus dictionary
            #by keys, then yields the values in that order
            self.corpus_box.insert(END,[getattr(word,d,'???') for d in word.descriptors])
        self.corpus_box.grid()

    def destroy_tier(self):

        word = self.corpus.random_word()
        if not word.tiers:
            MessageBox.showerror(message='No tiers have been added yet!')
            return

        self.destroy_tier_window = Toplevel()
        choose_tier = LabelFrame(self.destroy_tier_window, text='Select tier to remove')
        self.kill_tiers_list = Listbox(choose_tier)
        for tier_name in sorted(word.tiers):
            self.kill_tiers_list.insert(END,tier_name)
        self.kill_tiers_list.grid()
        kill_switch = Button(choose_tier, text='Remove', command=self.kill_tier)
        kill_all = Button(choose_tier, text='Remove all', command=self.kill_all_tiers)
        kill_switch.grid()
        kill_all.grid()
        choose_tier.grid()
        ok_button = Button(self.destroy_tier_window, text='Done', command=self.destroy_tier_window.destroy)
        ok_button.grid()

    def kill_tier(self):
        target = self.kill_tiers_list.get(self.kill_tiers_list.curselection())
        if target and self.show_warnings:
            msg = 'Are you sure you want to remove the {} tier?\nYou cannot undo this action.'.format(target)
            confirmed = MessageBox.askyesno(message=msg)
            if not confirmed:
                return

        for word in self.corpus:
            word.remove_tier(target)

        self.destroy_tier_window.destroy()
        self.main_screen_refresh()

    def kill_all_tiers(self):
        if self.show_warnings:
            msg = 'Are you sure you want to remove all the tiers?\nYou cannot undo this action'
            confirmed = MessageBox.askyesno(message=msg)
            if not confirmed:
                return

        kill_tiers = self.kill_tiers_list.get(0,END)
        for word in self.corpus:
            for tier in kill_tiers:
                word.remove_tier(tier)

        self.destroy_tier_window.destroy()
        self.main_screen_refresh()


    def create_tier(self):

        word = self.corpus.random_word()
        if not 'transcription' in word.descriptors:
            MessageBox.showerror(message='No transcription column was found in your corpus. This is required for Tiers.')
            return
        self.tier_window = Toplevel()
        self.tier_window.title('Create tier')
        tier_name_frame = LabelFrame(self.tier_window, text='What do you want to call this tier?')
        self.tier_name_entry = Entry(tier_name_frame)
        self.tier_name_entry.grid()
        tier_name_frame.grid(row=0,column=0)
        tier_frame = LabelFrame(self.tier_window, text='What features define this tier?')
        self.tier_feature_list = Listbox(tier_frame)
        for feature_name in self.corpus.get_features():
            self.tier_feature_list.insert(END,feature_name)
        self.tier_feature_list.grid(row=0,column=0)
        tier_frame.grid(row=1, column=0,sticky=N)
        add_plus_feature = Button(tier_frame, text='Add [+feature]', command=self.add_plus_tier_feature)
        add_plus_feature.grid(row=1,column=0)
        add_minus_feature = Button(tier_frame, text='Add [-feature]', command=self.add_minus_tier_feature)
        add_minus_feature.grid(row=2,column=0)
        selected_frame = LabelFrame(self.tier_window, text='Selected features')
        self.selected_tier_features = Listbox(selected_frame)
        self.selected_tier_features.grid()
        selected_frame.grid(row=1,column=1,sticky=N)
        remove_feature = Button(selected_frame, text='Remove feature', command=self.remove_tier_feature)
        remove_feature.grid()
        ok_button = Button(self.tier_window, text='Create tier', command=self.add_tier_to_corpus)
        preview_button = Button(self.tier_window, text='Preview tier', command=self.preview_tier)
        cancel_button = Button(self.tier_window, text='Cancel', command=self.tier_window.destroy)
        ok_button.grid(row=2,column=0)
        preview_button.grid(row=2,column=1)
        cancel_button.grid(row=2,column=2)

    def preview_tier(self):

        features = [feature for feature in self.selected_tier_features.get(0,END)]
        matches = list()
        for seg in self.corpus.inventory:
        #for key,value in self.corpus.specifier.matrix.items():
            if all(feature in self.corpus.specifier.matrix[seg.symbol] for feature in features):
                matches.append(seg.symbol)

        if not matches:
            matches = 'No segments in this corpus have this combination of feature values'
        else:
            matches.sort()
            m = list()
            x=0
            while matches:
                m.append(matches.pop(0))
                x+=1
                if x > 10:
                    x = 0
                    m.append('\n')
            matches = ' '.join(m)

        preview_window = Toplevel()
        preview_frame = LabelFrame(preview_window, text='This tier will contain these segments:')
        segs = Label(preview_frame, text=matches, justify=LEFT, anchor=W)
        segs.grid()
        preview_frame.grid()

    def add_tier_to_corpus(self):
        tier_name = self.tier_name_entry.get()
        selected_features = self.selected_tier_features.get(0,END)

        if not tier_name:
            MessageBox.showerror(message='Please enter a name for this tier')
            return
        if not selected_features:
            MessageBox.showerror(message='No features define this tier. Please select at least one feature')
            return

        for word in self.corpus:
            word.add_tier(tier_name, selected_features)

        self.tier_window.destroy()
        self.main_screen_refresh()


    def add_plus_tier_feature(self):
        try:
            feature_name = self.tier_feature_list.get(self.tier_feature_list.curselection())
            feature_name = '+'+feature_name
            self.selected_tier_features.insert(END,feature_name)
        except TclError:
            pass

    def add_minus_tier_feature(self):
        try:
            feature_name = self.tier_feature_list.get(self.tier_feature_list.curselection())
            feature_name = '-'+feature_name
            self.selected_tier_features.insert(END,feature_name)
        except TclError:
            pass

    def remove_tier_feature(self):
        feature = self.selected_tier_features.curselection()
        if feature:
            self.selected_tier_features.delete(feature)

    def change_warnings(self):
        self.show_warnings = not self.show_warnings

    def entropy(self,shortcut=None):
        #check if it's possible to do this analysis
        has_transcription = True
        has_frequency = True
        missing = list()
        if self.corpus.custom:
            random_word = self.corpus.random_word()
            if not 'transcription' in random_word.descriptors:
                has_transcription = False
                missing.append('transcription')
            if not 'frequency' in random_word.descriptors:
                has_frequency = False
                missing.append('token frequency')

            if self.show_warnings and not has_transcription:
                MessageBox.showwarning(message='Your corpus lacks a transcription column, which is necessary for this analysis')
                return

            elif self.show_warnings and not has_frequency:
                missing = ','.join(missing)
                MessageBox.showwarning(message='Your corpus lacks a token frequency count. This option will be disabled.')


        self.entropy_screen = Toplevel()
        self.entropy_screen.title('PPRM')

        ipa_frame = LabelFrame(self.entropy_screen, text='Sounds')
        segs = [seg.symbol for seg in self.corpus.inventory]
        segs.sort()
        seg1_frame = LabelFrame(ipa_frame, text='Choose first symbol')
        colmax = 10
        col = 0
        row = 0
        for seg in segs:
            seg_button = OldRadiobutton(seg1_frame, text=seg, variable=self.seg1_var, value=seg, indicatoron=0)
            seg_button.grid(row=row, column=col)
            col+=1
            if col > colmax:
                col = 0
                row += 1
        seg1_frame.grid()

        seg2_frame = LabelFrame(ipa_frame, text='Choose second symbol')
        colmax = 10
        col = 0
        row = 0
        for seg in segs:
            seg_button = OldRadiobutton(seg2_frame, text=seg, variable=self.seg2_var, value=seg, indicatoron=0)
            seg_button.grid(row=row, column=col)
            col+=1
            if col > colmax:
                col = 0
                row += 1
        seg2_frame.grid()


        option_frame = LabelFrame(self.entropy_screen, text='Options')

        tier_frame = LabelFrame(option_frame, text='Tier')
        tier_options = ['transcription']
        word = self.corpus.random_word()
        tier_options.extend([tier for tier in word.tiers])
        tier_options_menu = OptionMenu(tier_frame,self.entropy_tier_var,'transcription',*tier_options)
        tier_options_menu.grid()
        tier_frame.grid(row=0,column=0)

        typetoken_frame = LabelFrame(option_frame, text='Type or Token')
        type_button = Radiobutton(typetoken_frame, text='Count types', variable=self.entropy_typetoken_var, value='type')
        type_button.grid(sticky=W)
        type_button.invoke()
        token_button = Radiobutton(typetoken_frame, text='Count tokens', variable=self.entropy_typetoken_var, value='token')
        token_button.grid(sticky=W)
        if not has_frequency:
            token_button.configure(state=('disabled'))
        typetoken_frame.grid(row=1, column=0)

        ex_frame = LabelFrame(option_frame, text='Exhaustivity and uniqueness')
        check_exhaustive = Checkbutton(ex_frame, text='Check for exhaustivity', variable=self.entropy_exhaustive_var)
        check_exhaustive.grid()
        #check_exclusive = Checkbutton(ex_frame, text='Check for exclusivity', variable=self.entropy_exclusive_var)
        #check_exclusive.grid()
        check_uniqueness = Checkbutton(ex_frame, text='Check for uniqueness', variable=self.entropy_uniqueness_var)
        check_uniqueness.grid()
        ex_frame.grid(row=2, column=0)

        output_file_frame = LabelFrame(option_frame, text='Output file name')
        self.entropy_output_file_entry = Entry(output_file_frame, textvariable=self.entropy_filename_var)
        self.entropy_output_file_entry.grid()
        output_file_frame.grid(row=3, column=0)

        suggest_filename_button = Button(option_frame, text='Suggest a file name', command=self.suggest_filename)
        suggest_filename_button.grid()

        button_frame = Frame(self.entropy_screen)
        ok_button = Button(button_frame, text='Next step...', command=self.entropy_options)
        ok_button.grid(row=0, column=0)
        cancel_button = Button(button_frame, text='Cancel', command=self.cancel_entropy)
        cancel_button.grid(row=0, column=1)
        info_button = Button(button_frame, text='About this function...', command=self.entropy_info)
        info_button.grid(row=0, column=2)

        ipa_frame.grid(row=0, column=0, sticky=N)
        option_frame.grid(row=0, column=1, sticky=N)
        button_frame.grid(row=1,column=0)

    def add_plus_feature_lhs(self):
        try:
            feature_name = self.lhs_feature_list.get(self.lhs_feature_list.curselection())
            feature_name = '+'+feature_name
            self.lhs_selected_list.insert(END,feature_name)
        except TclError:
            pass

    def add_minus_feature_lhs(self):
        try:
            feature_name = self.lhs_feature_list.get(self.lhs_feature_list.curselection())
            feature_name = '-'+feature_name
            self.lhs_selected_list.insert(END,feature_name)
        except TclError:
            pass

    def add_plus_feature_rhs(self):
        try:
            feature_name = self.rhs_feature_list.get(self.rhs_feature_list.curselection())
            feature_name = '+'+feature_name
            self.rhs_selected_list.insert(END,feature_name)
        except TclError:
            pass


    def add_minus_feature_rhs(self):
        try:
            feature_name = self.rhs_feature_list.get(self.rhs_feature_list.curselection())
            feature_name = '-'+feature_name
            self.rhs_selected_list.insert(END,feature_name)
        except TclError:
            pass


    def cancel_entropy(self):
        self.seg1_var = StringVar()
        self.seg2_var = StringVar()
        self.entropy_filename_var = StringVar()
        self.entropy_screen.destroy()

    def entropy_options(self):

        seg1 = self.seg1_var.get()
        seg2 = self.seg2_var.get()
        fname = self.entropy_filename_var.get()

        if not (seg1 and seg2 and fname):
            MessageBox.showerror(message='Please ensure you have selected 2 segments, and entered a file name')
            return

        if not fname.endswith('.txt'):
            self.entropy_filename_var.set(self.entropy_filename_var.get()+'.txt')

        for child in self.entropy_screen.winfo_children():
            child.destroy()

        env_frame = LabelFrame(self.entropy_screen, text='Construct environment')

        lhs_frame = LabelFrame(env_frame, text='Left hand side')

        lhs_feature_frame = LabelFrame(lhs_frame, text='Feature-based environment')
        lhs_feature_entry_explanation = Label(lhs_feature_frame, text='Select one or more features to match')
        lhs_feature_entry_explanation.grid(row=0)
        self.lhs_feature_list = Listbox(lhs_feature_frame)
        for feature_name in self.corpus.get_features():
            self.lhs_feature_list.insert(END,feature_name)
        self.lhs_feature_list.grid(row=1, column=0)
        self.lhs_selected_list = Listbox(lhs_feature_frame)
        lhs_button_frame = Frame(lhs_feature_frame)
        add_plus = Button(lhs_button_frame, text='Add [+feature]', command=self.add_plus_feature_lhs)
        add_plus.grid(row=0,column=0)
        add_minus = Button(lhs_button_frame, text='Add [-feature]', command=self.add_minus_feature_lhs)
        add_minus.grid(row=1, column=0)
        clear_features = Button(lhs_button_frame, text='Clear list', command=lambda x=0:self.lhs_selected_list.delete(x,END))
        clear_features.grid(row=2, column=0)
        lhs_button_frame.grid(row=1,column=1)
        self.lhs_selected_list.grid(row=1, column=2)

        lhs_seg_frame = LabelFrame(lhs_frame, text='Segment-based environment')
        lhs_seg_entry_explanation = Label(lhs_seg_frame, text='Select a segment to match')
        lhs_seg_entry_explanation.grid()
        segs = [seg.symbol for seg in self.corpus.inventory]
        segs.sort()
        segs_frame = Frame(lhs_seg_frame)
        col = 0
        colmax = 8
        row = 0
        for seg in segs:
            seg_button = OldRadiobutton(segs_frame, text=seg, variable=self.lhs_seg_var, value=seg, indicatoron=0)
            seg_button.grid(row=row, column=col)
            col+=1
            if col > colmax:
                col = 0
                row += 1
        segs_frame.grid()
        self.lhs_seg_entry = Entry(lhs_seg_frame,textvariable=self.lhs_seg_var)
        self.lhs_seg_entry.grid()

        lhs_feature_frame.grid(row=0, column=0, sticky=N)
        lhs_seg_frame.grid(row=0, column=1, sticky=N)
        lhs_frame.grid(row=0, column=0, padx=3)


        #RIGHT HAND SIDE STARTS HERE
        rhs_frame = LabelFrame(env_frame, text='Right hand side')

        rhs_feature_frame = LabelFrame(rhs_frame, text='Feature-based environment')
        rhs_feature_entry_explanation = Label(rhs_feature_frame, text='Select one or more features to match')
        rhs_feature_entry_explanation.grid(row=0)
        self.rhs_feature_list = Listbox(rhs_feature_frame)
        for feature_name in self.corpus.get_features():
            self.rhs_feature_list.insert(END,feature_name)
        self.rhs_feature_list.grid(row=1, column=0)
        self.rhs_selected_list = Listbox(rhs_feature_frame)
        rhs_button_frame = Frame(rhs_feature_frame)
        add_plus = Button(rhs_button_frame, text='Add [+feature]', command=self.add_plus_feature_rhs)
        add_plus.grid(row=0,column=0)
        add_minus = Button(rhs_button_frame, text='Add [-feature]', command=self.add_minus_feature_rhs)
        add_minus.grid(row=1, column=0)
        clear_features = Button(rhs_button_frame, text='Clear list', command=lambda x=0:self.rhs_selected_list.delete(x,END))
        clear_features.grid(row=2, column=0)
        rhs_button_frame.grid(row=1,column=1)
        self.rhs_selected_list.grid(row=1, column=2)

        rhs_seg_frame = LabelFrame(rhs_frame, text='Segment-based environment')
        rhs_seg_entry_explanation = Label(rhs_seg_frame, text='Select a segment to match')
        rhs_seg_entry_explanation.grid()
        segs = [seg.symbol for seg in self.corpus.inventory]
        segs.sort()
        segs_frame = Frame(rhs_seg_frame)
        col = 0
        colmax = 8
        row = 0
        for seg in segs:
            seg_button = OldRadiobutton(segs_frame, text=seg, variable=self.rhs_seg_var, value=seg, indicatoron=0)
            seg_button.grid(row=row, column=col)
            col+=1
            if col > colmax:
                col = 0
                row += 1
        segs_frame.grid()
        self.rhs_seg_entry = Entry(rhs_seg_frame,textvariable=self.rhs_seg_var)
        self.rhs_seg_entry.grid()

        rhs_feature_frame.grid(row=0, column=0, sticky=N)
        rhs_seg_frame.grid(row=0, column=1, sticky=N)
        rhs_frame.grid(row=1, column=0, padx=3)

        env_frame.grid(row=0, column=0)

        add_env_to_list = Button(self.entropy_screen, text='Add this environment to list', command=self.confirm_entropy_options)
        add_env_to_list.grid(row=1, column=0)
        confirm_envs = Button(self.entropy_screen, text='Calculate entropy in selected environments', command=self.calculate_entropy)
        confirm_envs.grid(row=1, column=1)
        cancel_button = Button(self.entropy_screen, text='Cancel', command=self.entropy_screen.destroy)
        cancel_button.grid(row=1, column=2)

        selected_envs_frame = Frame(self.entropy_screen)
        selected_envs_frame.grid(row=0, column=1)
        selected_envs_label = Label(selected_envs_frame, text='Calculate entropy in the following environments:')
        selected_envs_label.grid()
        self.selected_envs_list = Listbox(selected_envs_frame)
        self.selected_envs_list.configure(width=40)
        self.selected_envs_list.grid()
        remove_env_button = Button(selected_envs_frame, text='Remove selected environment', command=self.remove_entropy_env)
        remove_env_button.grid()
        clear_envs = Button(selected_envs_frame, text='Remove all environments', command=lambda x=0:self.selected_envs_list.delete(x,END))
        clear_envs.grid()

    def remove_entropy_env(self):
        env = self.selected_envs_list.curselection()
        if env:
            self.selected_envs_list.delete(env)

    def confirm_entropy_options(self):
        lhs_features_chosen = self.lhs_selected_list.get(0)
        lhs_seg_chosen = self.lhs_seg_entry.get()
        rhs_features_chosen = self.rhs_selected_list.get(0)
        rhs_seg_chosen = self.rhs_seg_entry.get()
        if (lhs_features_chosen and lhs_seg_chosen) or (rhs_features_chosen and rhs_seg_chosen):
            MessageBox.showerror(message='You have selected both features and segments for an environment. Please choose only one.')
            return


        elif (not lhs_features_chosen) and (not lhs_seg_chosen) and (not rhs_features_chosen) and (not rhs_seg_chosen):
            #allow for no input on one side or the other, but not both
            MessageBox.showerror(message='Both sides of the environment are blank. Construct at least one side.')
            return

        formatted_env = list()

        if lhs_features_chosen:
            lhs_features = self.lhs_selected_list.get(0,END)
            formatted_env.append('[{}]'.format(','.join(lhs_features)))
            #self.selected_envs_list.insert(END,lhs_features)
            self.lhs_selected_list.delete(0,END)

        elif lhs_seg_chosen:
            lhs_seg = self.lhs_seg_entry.get()
            formatted_env.append(lhs_seg)
            #self.selected_envs_list.insert(END,lhs_seg)
            self.lhs_seg_entry.delete(0,END)

        else:
            formatted_env.append('')

        if rhs_features_chosen:
            rhs_features = self.rhs_selected_list.get(0,END)
            formatted_env.append('[{}]'.format(','.join(rhs_features)))
            #self.selected_envs_list.insert(END,rhs_features)
            self.rhs_selected_list.delete(0,END)

        elif rhs_seg_chosen:
            rhs_seg = self.rhs_seg_entry.get()
            formatted_env.append(rhs_seg)
            #self.selected_envs_list.insert(END,rhs_seg)
            self.rhs_seg_entry.delete(0,END)

        else:
            formatted_env.append('')

        formatted_env = '_'.join(formatted_env)
        self.selected_envs_list.insert(END,formatted_env)


    def calculate_entropy(self):
        check = self.selected_envs_list.get(0)
        if not check:
            MessageBox.showwarning(message='Please construct at least one environment')
            return

        self.calculating_entropy_screen = Toplevel()
        self.calculating_entropy_screen.title('Entropy results')
        status_label = Label(self.calculating_entropy_screen, text='Calculating entropy...')

        self.entropy_result_list = MultiListbox(self.calculating_entropy_screen, [('Environment',40), ('Entropy',40)])

        seg1 = self.seg1_var.get()
        seg2 = self.seg2_var.get()
        count_what = self.entropy_typetoken_var.get()

        env_list = [env for env in self.selected_envs_list.get(0,END)]
        env_matches, missing_words, overlapping_words = self.calculate_H(seg1,seg2,env_list)
        #print(env_matches)
        H_dict = dict()
        for env in env_matches:
            total_tokens = sum(env_matches[env][seg1]) + sum(env_matches[env][seg2])
            output_file_path = os.path.join(os.getcwd(), self.entropy_filename_var.get())
            with open(output_file_path, mode='a', encoding='utf-8') as f:
                if not total_tokens:
                    H_dict[env] = (0,0)
                    print('Environment {} does not exist in the corpus\n{}'.format(env, '='*15), file=f)
                    self.entropy_result_list.insert(END, [env, 'Environment not found'])
                else:
                    seg1_prob = sum(env_matches[env][seg1])/total_tokens
                    seg2_prob = sum(env_matches[env][seg2])/total_tokens
                    seg1_H = log(seg1_prob,2)*seg1_prob if seg1_prob > 0 else 0
                    seg2_H = log(seg2_prob,2)*seg2_prob if seg2_prob > 0 else 0
                    H = sum([seg1_H, seg2_H])*-1
                    self.entropy_result_list.insert(END, [env, str(H)])
                    H_dict[env] = (H, total_tokens)
                    print('Entropy for {} and {} in environment of {} is {}'.format(seg1, seg2, env, str(H)), file=f)
                    print('Frequency of {}: {}\nFrequency of {}: {}\nTotal count ({}): {}\n{}\n'.format(seg1, seg1_prob, seg2, seg2_prob, count_what, total_tokens,'='*15), file=f)

        if self.entropy_uniqueness_var.get() and overlapping_words:
            #envs are exhastive, but some overlap
            filename = 'overlapping_envs_'+self.entropy_filename_var.get().split('.')[0]+'.txt'
            with open(os.path.join(os.getcwd(),'ERRORS', filename), mode='w', encoding='utf-8') as f:

                print('The environments you selected are not unique, which means that some of them pick out the same environment in the same words.\r\n', file=f)
                print('For example, the environments of \'_[-voice]\' and \'_k\', are not unique. They overlap with each other, since /k/ is [-voice].\r\n',file=f)
                print('When your environments are not unique, the entropy calculation will be inaccurate, since some environments will be counted more than once.\r\n', file=f)
                print('This file contains all the words where this problem could arise.\r\n\r\n', file=f)
                print('Segments you selected: {}, {}\r'.format(seg1, seg2), file=f)
                print('Environments you selected: {}\r'.format(' ,'.join(str(env) for env in env_list)), file=f)
                print('Word\tRelevant environments (segmental level only)\r',file=f)
                for word in overlapping_words:
                    print('{}\t{}\r\n'.format(word,','.join([w for w in overlapping_words[word]])), file=f)

            text1 = 'Your environments are not unique, and two or more of them overlap.'
            text2 = 'This means that some environments will be counted more than once and your entropy values will not be reliable.'
            text3 = 'A text file called {} explaining this problem has been placed in your ERRORS folder'.format(filename)
            text4 = 'Do you want to carry on with the entropy calculation anyway?'
            do_entropy = MessageBox.askyesno(message='\n'.join([text1,text2,text3,text4]))
            if not do_entropy:
                return

        if self.entropy_exhaustive_var.get() and missing_words:
            #environments are unique but non-exhaustive
            filename = 'missing_words_'+self.entropy_filename_var.get().split('.')[0]+'.txt'
            with open(os.path.join(os.getcwd(),'ERRORS', filename), mode='w', encoding='utf-8') as f:

                print('The following words have at least one of the segments you are searching for, but it occurs in an environment not included in the list you selected\r', file=f)
                print('Segments you selected: {}, {}\r'.format(seg1, seg2), file=f)
                print('Environments you selected: {}\r'.format(' ,'.join(str(env) for env in env_list)), file=f)
                print('Word\tRelevant environments (segmental level only)\r',file=f)
                for word in missing_words:
                    line = '{}\t{}\r'.format(word, ','.join(str(wm) for wm in missing_words[word]))
                    print(line, file=f)

            if self.entropy_uniqueness_var.get() and overlapping_words:
                also = ' also '
            else:
                also = ' '
            text = 'Your selection of environments was{}non-exhaustive.'.format(also)
            text2 = 'This means some words contain the segments you selected, but they do not contain the environments you selected.'
            text3 = 'These words have been printed to the file {} in your ERRORS folder.'.format(filename)
            text4 = 'If you choose to carry on with the calculation, then environment-specific entropies will be accurate.'
            text5 = 'However, the weighted average entropy will not reflect the occurrence of the sounds in the non-included environments.'
            if self.entropy_uniqueness_var.get() and overlapping_words:
                text6 = 'The average will also not be accurate because your environments are non-unique.\nWould you still like to calculate entropy in the enviroments you supplied?'
            else:
                text6 = 'Would you still like to calculate entropy in the enviroments you supplied?'
            do_entropy = MessageBox.askyesno(message='\n\r'.join([text, text2, text3, text4, text5, text6]))
            if not do_entropy:
                return

        status_label.grid()
        self.entropy_result_list.grid()
        total_frequency = sum(value[1] for value in H_dict.values())

        output_file_path = os.path.join(os.getcwd(), self.entropy_filename_var.get())
        with open(output_file_path, mode='a', encoding='utf-8') as f:
            print('CORPUS: {}\n'.format(self.corpus.name), file=f)
            if not total_frequency:
                print('Weighted average entropy could not be calculated because none of the following environments were found:\n {}\n{}'.format(
                    ','.join(env for env in env_list),'='*15),
                    file=f)
                status_label.grid_forget()
                status_label.configure(text='Entropy could not be calculated because none of the selected environments were found in the corpus')
                status_label.grid()
            else:
                for env in env_matches:
                    H_dict[env] = H_dict[env][0] * (H_dict[env][1] / total_frequency)
                weighted_H = sum(H_dict[env] for env in H_dict)
                text = 'Weighted average entropy for {} and {} is {}, considering environments:\n{}\n'.format(
                        seg1, seg2, str(weighted_H), ','.join(env for env in env_list))
                print(text, file=f)
                status_label.grid_forget()
                status_label.configure(text='Weighted average entropy for /{}/ and /{}/ is {}'.format(seg1, seg2, weighted_H))
                status_label.grid()

    def calculate_H(self, seg1, seg2, user_supplied_envs):

        count_what = self.entropy_typetoken_var.get()
        user_supplied_envs = [self.formalize_env(env) for env in user_supplied_envs]
        env_matches = {'{}_{}'.format(user_env[0],user_env[1]):{seg1:[0], seg2:[0]} for user_env in user_supplied_envs}
        tier_name = self.entropy_tier_var.get()
        words_with_missing_envs = collections.defaultdict(list)
        words_with_overlapping_envs = collections.defaultdict(list)

        for word in self.corpus:
            word.set_string(tier_name) #this makes sure we loop over the right thing
            for pos,seg in enumerate(word):
                if not (seg == seg1 or seg == seg2):
                    continue

                word_env = word.get_env(pos)
                found_env_match = list()
                for user_env in user_supplied_envs:
                    key = '{}_{}'.format(user_env[0],user_env[1])
                    if self.match_to_env(word_env,user_env):
                        if count_what == 'type':
                            value = 1
                        elif count_what == 'token':
                            value = word.abs_freq
                        if seg == seg1:
                            env_matches[key][seg1].append(value)
                            #print(env_matches[key][seg1])
                        else:
                            #print('matched seg {} in word {}'.format(seg1, word))
                            env_matches[key][seg2].append(value)
                        found_env_match.append(user_env)

                if not found_env_match:
                    #found and environemnts with segs the user wants, but in
                    #an environement that was not supplied. Alert the user
                    #about this later
                    words_with_missing_envs[word.spelling].append(str(word_env))

                elif len(found_env_match) > 1:
                    #the user supplied environmnets that overlap, e.g. they want
                    #_[-voice] and also _k, but we shouldn't count this twice
                    #alert the user about this later
                    words_with_overlapping_envs[word.spelling].extend([str(env) for env in found_env_match])

        return env_matches, words_with_missing_envs, words_with_overlapping_envs


    def match_to_env(self,word_env,user_env):

        lhs,rhs = user_env
        l_match = False
        r_match = False

        if not lhs:
            l_match = True
            #empty side is a wildcard, so an automatic matches
        elif type(lhs)==str:
            if lhs == word_env.lhs.symbol:
                l_match = True
        else: #it's a feature list
            for feature in lhs:
                try:
                    match = feature[0] == word_env.lhs.features[feature[1:]]
                except KeyError:
                    break
                if not match:
                    break
            else:
                l_match = True
            #if all([word_env.lhs.features[feature]==lhs[feature] for feature in lhs]):
             #   l_match = True

        if not rhs:
            r_match = True
            #empty sides is a wildcard, so an automatic matches
        elif type(rhs)==str:
            if rhs == word_env.rhs.symbol:
                r_match = True
        else: #it's a feature list
            for feature in rhs:
                try:
                    match = feature[0] == word_env.rhs.features[feature[1:]]
                except KeyError:
                    break #occurs with word bounarires and other non-segmental things
                if not match:
                    break
            else:
                r_match = True
            #if all([word_env.rhs.features[feature]==rhs[feature] for feature in rhs]):
             #   r_match = True

        if l_match and r_match:
            #print('YEAH match for word {} on tier {}'.format(word.spelling, word_env))
            return True
        else:
            return False


    def formalize_env(self,env):

        #there's a problem where some feature names have underscores in them
        #so doing lhs,rhs=env.split('_') causes unpacking problems
        #this in an awakward work-around that checks to see if either side of
        #the environment is a list of features, by looking for brackets, then
        #splits by brackets if necessary. However, I can't split out any
        #starting brackets [ because I also use those for identifying lists
        #at a later point
        #otherwise, if its just segment envrionments, split by underscore

        if ']_[' in env:
            #both sides are lists
            lhs, rhs = env.split(']_')
        elif '_[' in env:
            #only the right hand side is a list of a features
            lhs, rhs = env.split('_', maxsplit=1)
        elif ']_' in env:
            #only the left hand side is a list of features
            lhs, rhs = env.split(']_')
        else: #both sides are segments
            lhs, rhs = env.split('_')

        if not lhs:
            pass
        elif lhs.startswith('['):
            lhs = lhs.lstrip('[')
            lhs = lhs.rstrip(']')
            #lhs = {feature[1:]:feature[0] for feature in lhs.split(',')}
            lhs = lhs.split(',')
        #else it's a segment, just leave it as the string it already is

        if not rhs:
            pass
        elif rhs.startswith('['):
            rhs = rhs.lstrip('[')
            rhs = rhs.rstrip(']')
            #rhs = {feature[1:]:feature[0] for feature in rhs.split(',')}
            rhs = rhs.split(',')
        #else it's a segment, just leave it as the string it already is

        #env = corpustools.Environment(lhs, rhs)
        return (lhs,rhs)

    def corpus_from_text(self):

        self.from_text_window = Toplevel()
        from_text_frame = LabelFrame(self.from_text_window, text='Create corpus from text')
        choose_file_frame = LabelFrame(from_text_frame, text='Select a file')
        self.from_text_entry = Entry(choose_file_frame)
        self.from_text_entry.grid()
        find_file = Button(choose_file_frame, text='Choose file...', command=self.navigate_to_text)
        find_file.grid(sticky=W)
        choose_file_frame.grid(sticky=W)

        new_name_frame = LabelFrame(from_text_frame, text='Name for new corpus (auto-suggested)')
        self.new_name_entry = Entry(new_name_frame)
        self.new_name_entry.grid(sticky=W)
        new_name_frame.grid(sticky=W)

        punc_frame = LabelFrame(from_text_frame, text='Select punctuation to ignore')
        row = 0
        col = 0
        colmax = 10
        for mark,var in zip(string.punctuation, self.punc_vars):
            check_button = Checkbutton(punc_frame, text=mark, variable=var)
            check_button.grid(row=row, column=col)
            col += 1
            if col > colmax:
                col = 0
                row += 1
        row += 1
        select_frame = Frame(punc_frame)
        select_all = Button(select_frame, text='Select all', command=lambda x=1: [var.set(x) for var in self.punc_vars])
        select_all.grid(row=0,column=0)
        deselect_all = Button(select_frame, text='Deselect all', command=lambda x=0: [var.set(x) for var in self.punc_vars])
        deselect_all.grid(row=0, column=1)
        select_frame.grid(row=row,column=0)
        punc_frame.grid(sticky=W)
        string_type_frame = LabelFrame(from_text_frame, text='Spelling or transcription')
        spelling_only = Radiobutton(string_type_frame, text='Corpus uses orthography',
                            value='spelling', variable=self.new_corpus_string_type)
        spelling_only.grid()
        spelling_only.invoke()
        trans_only = Radiobutton(string_type_frame, text='Corpus uses transcription',
                            value='transcription', variable=self.new_corpus_string_type)
        trans_only.grid()
        #both = Radiobutton(string_type_frame, text='Corpus has both spelling and transcription', value='both', variable=self.from_corpus_string_type)
        #both.grid()
        new_corpus_feature_frame = LabelFrame(string_type_frame, text='Feature system to use (if transcription exists)')
        new_corpus_feature_system = OptionMenu(new_corpus_feature_frame,#parent
            self.new_corpus_feature_system_var,#variable
            'spe',#selected option,
            *[fs for fs in self.all_feature_systems])#options in drop-down
        new_corpus_feature_system.grid()
        new_corpus_feature_frame.grid(sticky=W)
        string_type_frame.grid(sticky=W)
        ok_button = Button(from_text_frame, text='Create corpus', command=self.parse_text)
        cancel_button = Button(from_text_frame, text='Cancel', command=self.from_text_window.destroy)
        ok_button.grid()
        cancel_button.grid()
        from_text_frame.grid()

    def parse_text(self, delimiter=' '):

        if not os.path.isfile(self.from_text_entry.get()):
            MessageBox.showerror(message='Cannot find the file. Double check the path is correct.')
            return
        if os.path.isfile(os.path.join(os.getcwd(),self.new_name_entry.get())):
            carry_on = MessageBox.askyesno(message='The name you chose for the new corpus file already exists. Overwrite it?')
            if not carry_on:
                return

        string_type = self.new_corpus_string_type.get()
        word_count = collections.defaultdict(int)
        ignore_list = list()
        for mark,var in zip(string.punctuation, self.punc_vars):
            if var.get() == 1:
                ignore_list.append(mark)

        with open(self.from_text_entry.get(), encoding='utf-8', mode='r') as f:
            for line in f.readlines():
                if not line or line == '\n':
                    continue
                line = line.split(delimiter)
                for word in line:
                    word = word.strip()
                    word = [letter for letter in word if not letter in ignore_list]
                    if not word:
                        continue
                    if string_type == 'transcription':
                        word = '.'.join(word)
                    elif string_type == 'spelling':
                        word = ''.join(word)
                    word_count[word] += 1

        total_words = sum(word_count.values())
        outputfile = os.path.join(os.getcwd(), self.new_name_entry.get())

        with open(outputfile, encoding='utf-8', mode='w') as f:
            print('{},Frequency,Relative frequency,feature_system={}\r'.format(
                string_type,self.new_corpus_feature_system_var.get()), file=f)
            for word,freq in sorted(word_count.items()):
                print('{},{},{}\r'.format(word,freq,freq/total_words),file=f)

        MessageBox.showinfo(message='Corpus created! You can open it from File > Use custom corpus...')
        self.from_text_window.destroy()
##        see_corpus = MessageBox.askyesno(message='Corpus created! Do you want to open it now?\nYou can always open later from File>Use custom corpus...')
##        self.from_text_window.destroy()
##        if not see_corpus:
##            return
##        if self.corpus:
##            close_existing = MessageBox.askyesno(message='You already have a corpus open. Do you want to close it and see the new one?')
##            if not close_existing:
##                return
##
##        #at this point, the user wants to load the new corpus
##        name = self.new_name_entry.get()
##        name = name.split('.')[0]
##        self.create_custom_corpus(name, outputfile, delimiter=',')

    def navigate_to_text(self):
        text_file = FileDialog.askopenfilename(filetypes=(('Text files', '*.txt'),('Corpus files', '*.corpus')))
        if text_file:
            self.from_text_entry.delete(0,END)
            self.from_text_entry.insert(0, text_file)

            header,suggestion = os.path.split(text_file)
            suggestion = suggestion.split('.')[0]
            suggestion += '_corpus.txt'
            self.new_name_entry.delete(0,END)
            self.new_name_entry.insert(0,suggestion)

    def show_feature_system(self):

        if not self.corpus:
            MessageBox.showerror(message='No corpus selected')
            return

        if self.show_warnings:
            word = self.corpus.random_word()
            if word.tiers:
                msg = 'You have already created tiers based on a feature system.\nChanging feature systems may give unexpected results and is not recommended.'
                MessageBox.showwarning(message=msg)


        self.feature_screen = Toplevel()
        self.feature_screen.title('View/change feature system')
        feature_system_label = Label(self.feature_screen, text='FEATURE SYSTEM: {}'.format(self.feature_system))

        if self.feature_system == 'spe':
            filename = 'ipa2spe.txt'
            delimiter = ','
        elif self.feature_system == 'hayes':
            filename = 'ipa2hayes.txt'
            delimiter = '\t'
        else:
            filename = self.feature_system+'.txt'
            delimiter = ','

        with open(os.path.join(os.getcwd(), 'TRANS', filename), encoding = 'utf-8') as f:
            headers = f.readline()
            headers = headers.strip()
            headers = headers.split(delimiter)
            feature_chart = MultiListbox(self.feature_screen, [(h,5) for h in headers])
            for line in f:
                line = line.strip()
                if not line: #line is blank or just a newline
                    continue
                line = line.split(delimiter)
                symbol = line[0]
                line = [feature[0] for feature in line[1:]]
                data = [symbol]
                data.extend(line)
                feature_chart.insert(END, data)

        feature_chart.grid()
        choose_label = Label(self.feature_screen, text='Select a feature system')
        choose_label.grid()

        feature_menu = OptionMenu(self.feature_screen,#parent
                                self.feature_system_var,#variable
                                self.recently_selected_system,#selected option,
                                #'SPE', 'Hayes',#options in drop-down
                                *[fs for fs in self.all_feature_systems],
                                command=self.change_feature_system)
        feature_menu.grid()
        ok_button = Button(self.feature_screen, text='OK', command=self.confirm_change_feature_system)
        ok_button.grid()
        #cancel_button = Button(self.feature_screen, text='Cancel', command=self.feature_screen.destroy)
        #cancel_button.grid()


    def confirm_change_feature_system(self):

        try_system = self.feature_system_var.get()
        #try_system = try_system.lower()

        check_for_error = self.corpus.change_feature_system(try_system)
        #if there are any segments that cannot be represented in a given feature
        #system, then the corpus.change_feature_system() function returns them in a list
        #if check_for_error is an empty list, then feature changing was successful

        if check_for_error:
            #problems - print an error message
            filename = 'error_{}_{}.txt'.format(try_system, self.corpus.name)
            with open(os.path.join(os.getcwd(),'ERRORS',filename), encoding='utf-8', mode='w') as f:
                print('Some words in your corpus contain symbols that have no match in the \'{}\' feature system you\'ve selected.'.format(try_system),file=f)
                print('To fix this problem, open the features file in a text editor and add the missing symbols and appropriate feature specifications\r\n', file=f)
                print('All feature files are (or should be!) located in the TRANS folder. If you have your own feature file, just drop it into that folder before loading CorpusTools.\r\n\r\n', file=f)
                print('The following segments could not be represented:', file=f)
                for key in sorted(list(check_for_error.keys())):
                    words = sorted(check_for_error[key])
                    words = ','.join(words)
                    sep = '\r\n\n'
                    print('Symbol: {}\r\nWords: {}\r\n{}'.format(key,words,sep), file=f)
            msg1 = 'Not every symbol in your corpus can be interpreted with this feature system.'
            msg2 = 'A file called {} has been placed in your ERRORS folder explaining this problem in more detail.'.format(
            filename)
            msg = '\n'.join([msg1, msg2])
            MessageBox.showwarning(message=msg)
            self.feature_screen.destroy()
            self.feature_system = 'spe'

        else:
            #no problems - update feature system and change some on-screen info
            self.feature_system = try_system
            self.update_info_frame()
            self.feature_screen.destroy()

    def change_feature_system(self, event=None):
        word = self.corpus.random_word()
        if not hasattr(word, 'transcription'):
            MessageBox.showerror(message='No transcription column was found in your corpus.\nTranscription is necessary to use feature systems')
            return
        check_system = self.feature_system_var.get()
        #check_system = check_system.lower()
        if not check_system == self.feature_system:
            self.recently_selected_system = check_system
            self.feature_screen.destroy()
            self.show_feature_system()

def make_menus(root,app):

    menubar = Menu(root)
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label='Choose built-in corpus...', command=app.choose_corpus)
    filemenu.add_command(label='Use custom corpus...',
    command=app.choose_custom_corpus)
    filemenu.add_command(label='Create corpus from text...', command=app.corpus_from_text)
    filemenu.add_command(label='Save corpus as...', command=app.save_corpus_as)
    filemenu.add_checkbutton(label='Show warnings', onvalue=True, offvalue=False, variable=app.show_warnings, command=app.change_warnings)
    filemenu.add_command(label="Quit", command=app.quit, accelerator='Ctrl+Q')
    menubar.add_cascade(label="File", menu=filemenu)
    filemenu.invoke(4)#start with the checkmark for the 'show warning' option turned on

    corpusmenu = Menu(menubar, tearoff=0)
    corpusmenu.add_command(label='Search corpus...', command=app.search)
    corpusmenu.add_command(label='View/change feature system...', command=app.show_feature_system)
    corpusmenu.add_command(label='Add Tier...', command=app.create_tier)
    corpusmenu.add_command(label='Remove Tier...', command=app.destroy_tier)
    menubar.add_cascade(label='Corpus', menu=corpusmenu)

    calcmenu = Menu(menubar, tearoff=0)
    calcmenu.add_command(label='Calculate string similarity...', command=app.string_similarity)
    calcmenu.add_command(label='Calculate entropy...', command=app.entropy)
    calcmenu.add_command(labe='Calculate functional load...')
    menubar.add_cascade(label='Analysis', menu=calcmenu)

    helpmenu = Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Help...", command=app.donothing)
    helpmenu.add_command(label="About...", command=app.donothing)
    menubar.add_cascade(label="Help", menu=helpmenu)
    root.config(menu=menubar)

if __name__ == '__main__':
    root = Tk()
    root.title("CorpusTools v0.15")
    app = GUI(root)
    make_menus(root,app)
    root.bind_all('<Control-q>', app.quit)
    root.bind_all('<Control-h>', app.entropy)
    root.mainloop()