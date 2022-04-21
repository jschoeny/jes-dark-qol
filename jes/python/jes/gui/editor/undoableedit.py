# -*- coding: utf-8 -*-
"""
jes.editor.document
===================
An implementation of AbstractUndoableEdit for the UndoManager.

:copyright: (C) 2008 Buck Scharfnorth
:license:   GNU GPL v2 or later, see jes/help/JESCopyright.txt for details
"""
import javax.swing as swing

INSERT_EVENT = 1
REMOVE_EVENT = 2
REPLACE_EVENT = 3
MAX_UNDO_EVENTS_TO_RETAIN = 500

class UndoableEdit(swing.undo.AbstractUndoableEdit):

    ######################################################################
    # Function name: __init__
    # Parameters:
    #     -document: the JESEditorDocument object that is being used
    #     -editIsSignificant: whether an undo/redo will keep going until significant edit is found
    #     -eventType: identifies the type of event that occured (insert or remove)
    #     -offset: offset in the text that the event occured in
    #     -str: text that is being inserted or removed
    # Description:
    #     Creates an instance of the UndoableEdit class.
    #     The last 3 parameters are the same as the classic JES addUndoEvent method
    ######################################################################

    def __init__(self, document, editIsSignificant, eventType, offset, str, strOld=""):
        self.editIsSignificant = editIsSignificant
        self.undoEvent = [eventType, offset, str, strOld]
        self.document = document

######################################################################
# Function name: undo
# Description:
#     Undoes the last UndoableEdit from the document
######################################################################
    def undo(self):
        try:
            swing.undo.AbstractUndoableEdit.undo(self)
            lastEvent = self.getUndoEvent()
            if lastEvent[0] == INSERT_EVENT:
                self.document.remove(lastEvent[1], len(lastEvent[2]), 0)
                self.document.editor.select(lastEvent[1], lastEvent[1])
            elif lastEvent[0] == REMOVE_EVENT:
                self.document.insertString(
                    lastEvent[1], lastEvent[2], self.document.textAttrib, 0)
                self.document.editor.select(0, 0)
                if len(lastEvent[2]) > 1:
                    self.document.editor.select(lastEvent[1], lastEvent[1] + len(lastEvent[2]))
                else:
                    self.document.editor.select(lastEvent[1]+1, lastEvent[1]+1)
            else:
                self.document.remove(lastEvent[1], len(lastEvent[2]), 0)
                self.document.insertString(
                    lastEvent[1], lastEvent[3], self.document.textAttrib, 0)
                self.document.editor.select(0, 0)
                self.document.editor.select(lastEvent[1], lastEvent[1] + len(lastEvent[3]))
        except Exception, e:
            print "Exception thrown in undo"

######################################################################
# Function name: redo
# Description:
#     Redoes the last UndoableEdit from the document
######################################################################
    def redo(self):
        try:
            swing.undo.AbstractUndoableEdit.redo(self)
            lastEvent = self.getUndoEvent()
            if lastEvent[0] == REMOVE_EVENT:
                self.document.remove(lastEvent[1], len(lastEvent[2]), 0)
                self.document.editor.select(lastEvent[1], lastEvent[1])
            elif lastEvent[0] == INSERT_EVENT:
                self.document.insertString(
                    lastEvent[1], lastEvent[2], self.document.textAttrib, 0)
                self.document.editor.select(0, 0)
                if len(lastEvent[2]) > 1:
                    self.document.editor.select(lastEvent[1], lastEvent[1] + len(lastEvent[2]))
                else:
                    self.document.editor.select(lastEvent[1]+1, lastEvent[1]+1)
            else:
                self.document.remove(lastEvent[1], len(lastEvent[3]), 0)
                self.document.insertString(
                    lastEvent[1], lastEvent[2], self.document.textAttrib, 0)
                self.document.editor.select(0, 0)
                self.document.editor.select(lastEvent[1], lastEvent[1] + len(lastEvent[2]))
        except Exception, e:
            print "Exception thrown in redo"

######################################################################
# Function name: __init__
# Returns:
#     An UndoEvent based on this UndoableEdit
# Description:
#     Returns this UndoableEdit in the classic JES UndoEvent format
######################################################################
    def getUndoEvent(self):
        return self.undoEvent


    def isSignificant(self):
        return self.editIsSignificant == 1
