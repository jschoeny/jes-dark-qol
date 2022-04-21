# -*- coding: utf-8 -*-
"""
jes.editor
==========
This has the text editor widget at the center of JES (physically, if not
metaphorically).

:copyright: (C) 2002 Jason Ergle, Claire Bailey, David Raines, Joshua Sklare
:license:   GNU GPL v2 or later, see jes/help/JESCopyright.txt for details
"""
# Revisions:
# 5/29/08: added support for "redo" - Buck Scharfnorth
# 5/13/09: Changes for redesigning configuration writing from python to
# java -Buck

import JESConfig
import java.awt as awt
from java.awt.datatransfer import DataFlavor
import javax.swing as swing
import java.lang.String as String
import java.lang.Character as Character
import java.lang.Runnable as Runnable
from .document import JESEditorDocument

REPLACE_EVENT = 3
BACKGROUND_COLOR = awt.Color(28, 30, 31)
CARET_COLOR = awt.Color(78, 138, 226)
SELECTION_COLOR = awt.Color(63, 68, 80)
LINE_COLOR = awt.Color(61, 63, 71)
CURR_LINE_COLOR = awt.Color(255, 255, 255, 15)

MODIFIED_TITLE = " **"

class RunnableWrapper(Runnable):
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.func(*self.args, **self.kwargs)

def runswing(func):
    """Schedules the given function for execution in the Event Dispatch Thread."""
    def wrapper(*args, **kwargs):
        swing.SwingUtilities.invokeLater(RunnableWrapper(func, *args, **kwargs))
    return wrapper

class JESEditor(swing.JTextPane,
                swing.event.DocumentListener,
                swing.event.CaretListener,
                awt.event.FocusListener,
                swing.event.MouseInputListener):
    ##########################################################################
    # Function name: __init__
    # Parameters:
    #     -gui: JESUI object that this object is associated with
    # Return:
    #     An instance of the JESEditor class.
    # Description:
    #     Creates an instance of the JESEditor class.
    ##########################################################################

    def __init__(self, gui):
        self.gui = gui
        self.program = gui.program
        self.setContentType("text/plain")
        self.setDocument(JESEditorDocument(self))
        self.addCaretListener(self)
        self.addFocusListener(self)
        self.addMouseListener(self)
        self.addMouseMotionListener(self)
        self.modified = 0
        self.boxX = 0
        self.boxY = 0
        self.boxWidth = 0
        self.boxHeight = 0
        self.indentLines = []
        self.linePrev = 0
        self.darkMode = 0
        self.focused = False
        self.matchingCharPos = []
        self.selectionStarted = False
        self.disableMatchingChar = False
        self.lastSavedText = ""
        self.copyNumSpaces = 0
        self.lastCopyFromSelf = ""
        self.setMargin(awt.Insets(0, 4, 0, 0))
        self.setDarkMode(JESConfig.getInstance().getBooleanProperty(JESConfig.CONFIG_DARK))
        self.getCaret().setBlinkRate(400)

        # try:
        #     self.setDropMode(swing.DropMode.USE_SELECTION)
        # except Exception, e:
        #     print("ERROR: Drop mode not enabled.")


    def setDarkMode(self, enable):
        caret = self.getCaret()
        if enable:
            self.darkMode = 1
            self.document.setDarkMode(1)
            self.setBackground(BACKGROUND_COLOR)
            self.setCaretColor(CARET_COLOR)
            self.setSelectionColor(SELECTION_COLOR)
            # caret.setSize(2, int(caret.getHeight()))
            # caret.width = 4
            self.putClientProperty("caretWidth", 2)
        else:
            self.darkMode = 0
            self.document.setDarkMode(0)
            self.setBackground(awt.Color.white)
            self.setCaretColor(awt.Color.black)
            self.setSelectionColor(awt.Color(165, 205, 255))
            # caret.setSize(1, int(caret.getHeight()))
            self.putClientProperty("caretWidth", 1)


##########################################################################
# Function name: showErrorLine
# Parameters:
#      -lineNumber
# Description:
#     When this function is called, the specified line will be highlighted so
#     that the user can tell which line contains an error.
##########################################################################
    def showErrorLine(self, lineNumber):
        self.document.showErrorLine(lineNumber)

##########################################################################
# Function name: undo
# Description:
#     This function can be called to undo the last text modification that was
#     performed.
##########################################################################
    def undo(self):
        self.document.undo()

##########################################################################
# Function name: redo
# Description:
#     This function can be called to redo the last text modification that was
#     performed.
##########################################################################
    def redo(self):
        self.document.redo()


    def copy(self):
        start = self.getSelectionStart()
        end = self.getSelectionEnd()
        selection = self.getSelectedText()
        text = self.getText()
        scan = start
        while scan > 0 and text[scan] != '\n':
            scan -= 1
        if text[scan] == '\n':
            scan += 1
        selectionNew = text[scan:end]
        numSpaces = len(selectionNew) - len(selectionNew.lstrip())

        self.copyNumSpaces = numSpaces
        self.lastCopyFromSelf = selection

        self.super__copy()


    def paste(self):
        textToPaste = self.getContentToPaste(self)

        if not textToPaste:
            return

        selfCopy = False
        if self.copyNumSpaces > 0 and textToPaste == self.lastCopyFromSelf:
            textToPaste = (' ' * self.copyNumSpaces) + textToPaste
            selfCopy = True
        # Determine where to put the text, and type!
        # (We let the DocumentFilter determine the final location.)
        start, end = self.getSelectionStart(), self.getSelectionEnd()

        doc = self.document
        text = self.getText()
        if start == end:
            numSpaces = 0
            if start > 0:
                if text[start-1] == ':' and textToPaste[0] == '\n':
                    numSpaces = 2
                scan = start - 1
                while scan > 0 and text[scan] != '\n':
                    scan -= 1
                if text[scan] == '\n':
                    scan += 1
                rowText = text[scan:start]
                newRowText = rowText.lstrip()
                numSpaces += len(rowText) - len(newRowText)

            minSpaces = 0
            if textToPaste.count('\n') > 0:
                res = [i for i in range(len(textToPaste)) if textToPaste.startswith('\n', i)]
                res.append(len(textToPaste))
                if 0 not in res:
                    res.insert(0, -1)

                for i in range(len(res)-1):
                    rowText = textToPaste[res[i]+1:res[i+1]]
                    newRowText = rowText.lstrip()
                    if i == 0 and res[i] == 0:
                        if newRowText.startswith('if ') or newRowText.startswith('elif '):
                            numSpaces -= 2
                    if i == 0:
                        minSpaces = len(rowText) - len(newRowText)
                    else:
                        minSpaces = min(minSpaces, len(rowText) - len(newRowText))
                if minSpaces > 0:
                    textToPaste = textToPaste.replace('\n' + (' ' * minSpaces), '\n')

            textToPaste = textToPaste.replace('\n', '\n' + (' ' * numSpaces))
            if selfCopy:
                textToPaste = textToPaste[self.copyNumSpaces:]
            doc.insertString(self.getCaretPosition(), textToPaste, None)
        elif end > start:
            self.replaceSelection(textToPaste)


    def getContentToPaste(self, forComponent):
        clipboard = awt.Toolkit.getDefaultToolkit().getSystemClipboard()
        clipContents = clipboard.getContents(forComponent)

        for flavor in clipContents.getTransferDataFlavors():
            if DataFlavor.stringFlavor.equals(flavor):
                return clipContents.getTransferData(flavor)

        return None


    def decreaseIndent(self):
        selection = self.getSelectedText()
        if selection != None:
            doc = self.document
            text = self.getText()
            startPos = self.getSelectionStart()
            endPos = self.getSelectionEnd()
            while startPos > 0 and text[startPos] != '\n':
                startPos -= 1
            if startPos != 0:
                startPos += 1

            textBefore = text[startPos:endPos]
            if text[startPos:startPos+2] == '  ':
                doc.remove(startPos, 2, 0)

            selStart = self.getSelectionStart()
            selEnd = self.getSelectionEnd()
            off = selection.count('\n') * 2
            text = self.getText()
            i = selStart
            num = 0
            while i + 3 < selEnd:
                if text[i:i+3] == '\n  ':
                    doc.remove(i - (num*2) + 1, 2, 0)
                    num += 1
                i += 1
            self.select(selStart, selEnd - (num*2))
            text = self.getText()
            textAfter = text[startPos:selEnd - (num*2)]
            self.document.addUndoEvent(REPLACE_EVENT, startPos, textAfter, 1, textBefore)
        else:
            text = self.getText()
            startPos = self.getCaretPosition()
            scan = startPos - 1
            end = startPos
            while scan > 0 and text[scan] != '\n':
                scan -= 1
            if scan != 0:
                scan += 1
            while end < len(text) and text[end].isspace():
                end += 1

            rowText = text[scan:end]
            newRowText = rowText.lstrip()
            numSpaces = len(rowText) - len(newRowText)
            if numSpaces > 0 and len(newRowText) == 0:
                n = 2 - (numSpaces % 2)
                self.document.remove(scan, n)
                if startPos != len(text) and text[startPos].isspace():
                    newText = self.getText()
                    if not newText[startPos-1].isspace():
                        startPos -= 1
                    self.select(startPos, startPos)


    def toggleComment(self):
        selection = self.getSelectedText()
        doc = self.document
        text = self.getText()
        if len(text) > 0:
            selStart = self.getSelectionStart()
            selEnd = self.getSelectionEnd()
            startPos = selStart
            endPos = selEnd
            while startPos > 0 and text[startPos] != '\n':
                startPos -= 1
            if selection == None or selection.count('\n') == 0:
                rowText = text[startPos:selEnd]
                newRowText = rowText.lstrip()
                numSpaces = len(rowText) - len(newRowText)
                if newRowText[0] == '#':
                    doc.remove(startPos + numSpaces, 2)
                else:
                    doc.insertString(startPos + numSpaces, '# ')
            else:
                while startPos > 0 and text[startPos] != '\n':
                    startPos -= 1
                while endPos < len(text) and text[endPos] != '\n':
                    endPos += 1
                res = [i for i in range(startPos, endPos) if text.startswith('\n', i)]
                if startPos == 0:
                    res.insert(0, -1)

                minSpaces = 0
                uncomment = True
                for i in range(len(res)-1):
                    rowText = text[res[i]+1:res[i+1]]
                    newRowText = rowText.lstrip()
                    if i == 0:
                        minSpaces = len(rowText) - len(newRowText)
                    else:
                        minSpaces = min(minSpaces, len(rowText) - len(newRowText))
                    if len(newRowText) > 0 and newRowText[0] != '#':
                        uncomment = False

                self.select(max(0,res[0]), selEnd)
                selection = self.getSelectedText()
                offset = 2
                if uncomment:
                    selection = selection.replace('\n' + (' ' * minSpaces) + '# ', '\n' + (' ' * minSpaces))
                    if startPos == 0:
                        selection = selection.replace('# ', '', 1)
                    offset = -2
                else:
                    if startPos == 0:
                        selection = (' ' * minSpaces) + '# ' + selection
                    selection = selection.replace('\n' + (' ' * minSpaces), '\n' + (' ' * minSpaces) + '# ')
                self.replaceSelection(selection)
                self.select(selStart + offset, selEnd + (len(res) * offset))


##########################################################################
# Function name: getScrollableTracksViewportWidth
# Description:
#     Overrides base getScrollableTracksViewportWidth function to disable
#     word-wrapping.
##########################################################################
    def getScrollableTracksViewportWidth(self):
        parent = self.getParent()
        ui = self.getUI()
        return ui.getPreferredSize(self).width <= parent.getSize().width


##########################################################################
# Other MouseListener functions implemented to fix background repainting
#     issues
##########################################################################
    def mousePressed(self, e):
        self.repaint()
        self.gui.gutter.repaint()
        if -1 not in self.matchingCharPos:
            if len(self.matchingCharPos) % 2 == 0:
                while len(self.matchingCharPos) > 0:
                    pos1 = self.matchingCharPos.pop()
                    pos2 = self.matchingCharPos.pop()
                    self.document.setCharacterAttributes(pos1, 1, self.document.textAttrib, True)
                    self.document.setCharacterAttributes(pos2, 1, self.document.textAttrib, True)
            self.matchingCharPos = []

    def mouseEntered(self, e):
        pass

    def mouseClicked(self, e):
        pass

    def mouseExited(self, e):
        pass

    def mouseReleased(self, e):
        pass

    def mouseDragged(self, e):
        if not self.selectionStarted and e.getButton() == awt.event.MouseEvent.BUTTON1:
            caret = self.getCaret()
            if caret.getDot() != caret.getMark():
                if -1 not in self.matchingCharPos:
                    if len(self.matchingCharPos) % 2 == 0:
                        while len(self.matchingCharPos) > 0:
                            pos1 = self.matchingCharPos.pop()
                            pos2 = self.matchingCharPos.pop()
                            self.document.setCharacterAttributes(pos1, 1, self.document.textAttrib, True)
                            self.document.setCharacterAttributes(pos2, 1, self.document.textAttrib, True)
                    self.matchingCharPos = []
                self.repaint()
                self.selectionStarted = True

    def mouseMoved(self, e):
        pass


##########################################################################
# Function name: caretUpdate
# Parameters:
#      -e: event object containing infomation about the caret event
# Description:
#     Catches the caretUpdate event for the JESEditorClass.  It then updates
#     the gui status bar with the current row and column.
##########################################################################
    def caretUpdate(self, e):
        self.selectionStarted = False
        offset = self.getCaretPosition()
        defaultElement = self.document.getDefaultRootElement()
        elementIndex = defaultElement.getElementIndex(offset)
        element = defaultElement.getElement(elementIndex)
        row = offset - element.getStartOffset() + 1
        col = elementIndex + 1
        self.gui.UpdateRowCol(row, col)

        caret = self.getCaret()
        if -1 not in self.matchingCharPos:
            if not self.disableMatchingChar:
                prevPos1 = -1
                prevPos2 = -1
                if (len(self.matchingCharPos) > 0):
                    prevPos1 = self.matchingCharPos.pop()
                    prevPos2 = self.matchingCharPos.pop()
                if len(self.matchingCharPos) % 2 == 0:
                    while len(self.matchingCharPos) > 0:
                        pos1 = self.matchingCharPos.pop()
                        pos2 = self.matchingCharPos.pop()
                        self.document.setCharacterAttributes(pos1, 1, self.document.textAttrib, True)
                        self.document.setCharacterAttributes(pos2, 1, self.document.textAttrib, True)
                self.matchingCharPos = []

                if caret.getDot() - caret.getMark() <= 1:
                    text = self.getText()
                    textLen = len(text)
                    line = text[element.getStartOffset():element.getEndOffset()]
                    commentPos = line.find('#')
                    if (commentPos == -1 or offset < commentPos):
                        charNext = ''
                        charPrev = ''
                        if offset < textLen:
                            charNext = text[offset:offset+1]
                        if offset > 0:
                            charPrev = text[offset-1:offset]

                        if prevPos1 != -1 and prevPos2 != -1:
                            if (
                                charNext == charPrev
                                or (offset != prevPos1 and offset != prevPos2
                                    and offset - 1 != prevPos1 and offset - 1 != prevPos2)
                            ):
                                self.document.setCharacterAttributes(prevPos1, 1, self.document.textAttrib, True)
                                self.document.setCharacterAttributes(prevPos2, 1, self.document.textAttrib, True)

                        if charNext == '(' or charPrev == '(':
                            n = 0 if charNext == '(' and charNext != charPrev else 1
                            self.getMatchingChar(offset - n, text, '(', ')', True)
                        elif charNext == ')' or charPrev == ')':
                            n = 0 if charPrev == ')' and charNext != charPrev else 1
                            self.getMatchingChar(offset + n, text, '(', ')', False)
                        elif charNext == '[' or charPrev == '[':
                            n = 0 if charNext == '[' and charNext != charPrev else 1
                            self.getMatchingChar(offset - n, text, '[', ']', True)
                        elif charNext == ']' or charPrev == ']':
                            n = 0 if charPrev == ']' and charNext != charPrev else 1
                            self.getMatchingChar(offset + n, text, '[', ']', False)
                        else:
                            self.checkIfInKeyword()
                    else:
                        self.checkIfInKeyword()
                else:
                    if prevPos1 != -1 and prevPos2 != -1:
                        self.document.setCharacterAttributes(prevPos1, 1, self.document.textAttrib, True)
                        self.document.setCharacterAttributes(prevPos2, 1, self.document.textAttrib, True)
                    self.checkIfInKeyword()
            else:
                self.clearMatchingChars()
                self.checkIfInKeyword()
        else:
            self.matchingCharPos.pop()
            self.checkIfInKeyword()

        if self.linePrev != elementIndex and JESConfig.getInstance().getBooleanProperty(JESConfig.CONFIG_GUTTER):
            self.linePrev = elementIndex
            self.gui.gutter.repaint()
        if not JESConfig.getInstance().getBooleanProperty(JESConfig.CONFIG_BLOCK):
            self.updateBox(offset)
            self.calculateLines()
            # print str(self.isBlank(offset))
            self.repaint()
        else:
            self.boxX = 0
            self.indentLines = []
            self.repaint()

    @runswing
    def highlightMatchingChars(self, startChar, endChar):
        self.document.setCharacterAttributes(startChar, 1, self.document.matchingAttrib, True)
        self.document.setCharacterAttributes(endChar, 1, self.document.matchingAttrib, True)
        self.matchingCharPos.append(startChar)
        self.matchingCharPos.append(endChar)

    # Clears the stored matching chars for highlighting
    def clearMatchingChars(self):
        while -1 in self.matchingCharPos:
            self.matchingCharPos.pop()
        while len(self.matchingCharPos) > 0:
            pos1 = self.matchingCharPos.pop()
            pos2 = self.matchingCharPos.pop()
            self.document.setCharacterAttributes(pos1, 1, self.document.textAttrib, True)
            self.document.setCharacterAttributes(pos2, 1, self.document.textAttrib, True)

    # Check if cursor is on matching char, i.e. (),[], and highlight
    def getMatchingChar(self, offset, text, leftChar, rightChar, startLeft):
        textLen = len(text)
        if startLeft:
            numOff = 0
            end = offset + 1
            while end < textLen and (numOff > 0 or text[end] != rightChar):
                if text[end] == leftChar:
                    numOff += 1
                elif text[end] == rightChar:
                    numOff -= 1
                end += 1
            if end < textLen and end - offset > 1:
                self.highlightMatchingChars(offset, end)
            self.checkIfInKeyword()
        else:
            offset -= 1
            numOff = 0
            start = offset - 1
            while start >= 0 and (numOff > 0 or text[start] != leftChar):
                if text[start] == rightChar:
                    numOff += 1
                elif text[start] == leftChar:
                    numOff -= 1
                start -= 1
            if start >= 0 and offset - start > 1:
                self.highlightMatchingChars(start, offset)
            self.checkIfInKeyword()


    # see if we can describe the word we are on with the caret
    def checkIfOnKeyword(self, offset=-1, argNum=-1):
        if offset == -1:
            offset = self.getCaretPosition()
        currentPosition = offset
        startPosition = 0
        endPosition = 0

        if currentPosition > 0 and not (Character.isLetter(String(self.getText(currentPosition, 1)).charAt(0)) or self.getText(currentPosition, 1) == '_'):
            currentPosition -= 1

        while currentPosition > 0 and (Character.isLetter(String(self.getText(currentPosition, 1)).charAt(0)) or self.getText(currentPosition, 1) == '_'):
            currentPosition -= 1

        startPosition = currentPosition
        currentPosition = offset

        while currentPosition < self.document.getLength() and (Character.isLetter(String(self.getText(currentPosition, 1)).charAt(0)) or self.getText(currentPosition, 1) == '_'):
            currentPosition += 1

        endPosition = currentPosition

        keyword = self.getText(startPosition, endPosition - startPosition + 1)

        # the above selects more text than is needed sometimes, so we prune the
        # edges
        if not (keyword[0].isalpha() or keyword[0] == '_'):
            keyword = keyword[1:]

        if len(keyword) > 0:
            if not keyword[len(keyword) - 1].isalpha():
                keyword = keyword[:len(keyword) - 1]

            return self.gui.UpdateToolbarHelp(keyword, argNum)
        return False

    # see if we can describe the word before the () which the caret is inside of
    def checkIfInKeyword(self, offset=-1):
        if offset == -1:
            offset = self.getCaretPosition()
        if not self.checkIfOnKeyword(offset):
            text = self.getText()
            if len(text) == 0:
                return
            if offset >= len(text):
                offset = len(text) - 1

            caretPos = offset
            offset -= 1
            numOff = 0

            while offset > 1:
                if text[offset] == ')':
                    numOff += 1
                elif text[offset] == '(':
                    if numOff == 0:
                        break
                    numOff -= 1
                offset -= 1

            end = caretPos
            numOff = 0
            while end < len(text):
                if text[end] == '(':
                    numOff += 1
                elif text[end] == ')':
                    if numOff == 0:
                        break
                    numOff -= 1
                end += 1
            if end == len(text):
                return

            numOff = 0
            if offset > 1:
                search = offset + 1
                argNum = 0
                if end < len(text) and ',' in text[search:end]:
                    while search < caretPos+1:
                        if numOff == 0 and text[search-1] == ',':
                            argNum += 1
                        if text[search] == '(':
                            numOff += 1
                        elif text[search] == ')':
                            numOff -= 1
                        search += 1
                self.checkIfOnKeyword(offset - 1, argNum)

    # Find and store x,y positions for indentation lines
    def calculateLines(self):
        self.indentLines = []
        text = self.getText()
        res = [i for i in range(len(text)) if text.startswith('\n', i)]
        res.insert(0, -1)
        res.append(len(text))
        indent = []
        for i in range(len(res)-1):
            rowText = text[res[i]+1:res[i+1]]
            newRowText = rowText.lstrip()
            if len(rowText) == 0:
                indent.append(-1)
            else:
                indent.append(len(rowText) - len(newRowText))

        defaultElement = self.document.getDefaultRootElement()

        if len(indent) > 1:
            for i in range(len(indent)-1):
                if indent[i] == -1 or indent[i+1] == -1:
                    continue

                endRow = i
                for y in range(i+1, len(indent)):
                    if indent[y] <= indent[i] and indent[y] != -1:
                        break
                    endRow = y
                if endRow == len(indent)-1 and indent[endRow] == -1 and self.getCaretPosition() == len(text):
                    endRow -= 1

                if endRow > i:
                    topStart = defaultElement.getElement(i+1).getStartOffset()
                    topStartCoord = self.modelToView(topStart + indent[i])

                    bottomStart = defaultElement.getElement(endRow).getStartOffset()
                    bottomStartCoord = self.modelToView(bottomStart + indent[i])

                    # Set Coordinates
                    yPos = bottomStartCoord.y + bottomStartCoord.height
                    line = [topStartCoord.x + 4, topStartCoord.y, yPos]
                    self.indentLines.append(line)



##########################################################################
# Function name: removeBox
# Description:
#     Sets the boxX to 0, disabling the box, and repaints the text area
##########################################################################
    def removeBox(self):
        self.boxX = 0
        self.repaint()

##########################################################################
# Function name: addBox
# Description:
#     Explicitly draws the box without a caretUpdate event.
##########################################################################
    def addBox(self):
        offset = self.getCaretPosition()
        defaultElement = self.document.getDefaultRootElement()
        elementIndex = defaultElement.getElementIndex(offset)
        row = offset - \
            defaultElement.getElement(elementIndex).getStartOffset() + 1
        col = elementIndex + 1
        self.gui.UpdateRowCol(row, col)
        self.updateBox(offset)
        self.repaint()

##########################################################################
# Function name: updateBox
# Parameters:
#     -caretPos: the position of the caret in the document
# Description:
#     Calculates the bounds for the box around the block where the caret is.
#     Iterates up the elements until it finds a line with fewer spaces at the
#     begining and set that as the first line.  Then, it searches down until it
#     finds a line with fewer spaces at the beginning, and sets that as the last
#     line.  Also, as it looks through the lines, it finds the longes one and
#     sets the width to that.
##########################################################################
    def updateBox(self, offset):
        try:
            defaultElement = self.document.getDefaultRootElement()
            rowIndex = defaultElement.getElementIndex(offset)
            rowStart = defaultElement.getElement(rowIndex).getStartOffset()
            rowEnd = defaultElement.getElement(rowIndex).getEndOffset() - 1
            indentLevel = self.getNumSpaces(rowStart)
            width = self.modelToView(rowEnd).x
            if (indentLevel == 0):
                self.boxX = 0
                self.boxY = 0
                self.boxWidth = 0
                self.boxHeight = 0
            else:
                # Get the top row in the same block
                topIndex = rowIndex
                while topIndex > 1:
                    if self.getNumSpaces(defaultElement.getElement(topIndex - 1).getStartOffset()) >= indentLevel \
                            or self.isBlank(defaultElement.getElement(topIndex - 1).getStartOffset()):
                        topIndex = topIndex - 1
                        end = self.modelToView(
                            defaultElement.getElement(topIndex).getEndOffset() - 1).x
                        if end > width:
                            width = end
                    else:
                        break
                topStart = defaultElement.getElement(topIndex).getStartOffset()
                rowStart = defaultElement.getElement(rowIndex).getStartOffset()
                topStartWidth = self.modelToView(rowStart + indentLevel)
                topStartCoord = self.modelToView(topStart + indentLevel)

                # Get the bottom row in the same block
                bottomSpaced = 0
                bottomIndex = rowIndex
                bottomLast = bottomIndex
                while bottomIndex < defaultElement.getElementCount() - 1:
                    bottomSpaced = self.isBlank(
                        defaultElement.getElement(bottomIndex + 1).getStartOffset())
                    if self.getNumSpaces(defaultElement.getElement(bottomIndex + 1).getStartOffset()) >= indentLevel or bottomSpaced:
                        bottomIndex = bottomIndex + 1
                        end = self.modelToView(
                            defaultElement.getElement(bottomIndex).getEndOffset() - 1).x
                        if bottomSpaced == 0:
                            bottomLast = bottomIndex
                        if end > width:
                            width = end
                    else:
                        break
                bottomStart = defaultElement.getElement(
                    bottomLast).getStartOffset()
                bottomStartCoord = self.modelToView(bottomStart + indentLevel)

                # Set Coordinates
                self.boxX = topStartWidth.x - 1
                self.boxY = topStartCoord.y
                self.boxHeight = bottomStartCoord.y + \
                    bottomStartCoord.height - topStartCoord.y
                self.boxWidth = width - topStartCoord.x + 15

        except Exception, e:
            pass

##########################################################################
# Function name: getNumSpaces
# Parameters:
#     -offset: an index on the line to get the number of spaces on
# Description:
#     Returns the number of spaces on the beginning of a line.
##########################################################################
    def getNumSpaces(self, offset):
        defaultElement = self.document.getDefaultRootElement()
        rowIndex = defaultElement.getElementIndex(offset)
        rowStart = defaultElement.getElement(rowIndex).getStartOffset()
        rowEnd = defaultElement.getElement(rowIndex).getEndOffset() - 1
        rowText = self.getText(rowStart, rowEnd - rowStart)  # .expandtabs()
        newRowText = rowText.lstrip()
        return (len(rowText) - len(newRowText))

##########################################################################
# Function name: isBlank
# Parameters:
#     -offset: an index on the line to determine "blankness" or "blankitude"
# Description:
#     Determines if a line is blank, or just has spaces on it.  Returns 1 if
#     the line is blank, and 0 if it has text on it.
##########################################################################
    def isBlank(self, offset):
        try:
            defaultElement = self.document.getDefaultRootElement()
            rowIndex = defaultElement.getElementIndex(offset)
            rowStart = defaultElement.getElement(rowIndex).getStartOffset()
            rowEnd = defaultElement.getElement(rowIndex).getEndOffset()
            # print "Start: " + str(rowStart) + "   End: " + str(rowEnd)
            text = self.document.getText(rowStart, rowEnd - rowStart)
            for char in text:
                if char != " " and char != "\n":
                    return 0
            return 1
        except Exception, e:
            return 0

##########################################################################
# Function name: setText
# Parameters:
#      -text: text that is being put into the editor
# Description:
#     Overrides the default setText function of the JTextPane.  It resets the
#     modified flag to false, so that the user is not prompted to save on load
#     (unless they make a modification to the file).
##########################################################################
    def setText(self, text):
        self.modified = 0
        self.lastSavedText = text
        self.gui.loadButton.enabled = 0
        self.gui.saveButton.enabled = 1
        swing.JTextPane.setText(self, text)
        self.setTitleModified(False)
        self.setCaretPosition(0)
        self.document.undoManager.discardAllEdits()

##########################################################################
# Function name: paint
# Parameters:
#      -g: the graphics object that will be drawn
# Description:
#     Overrides the Java paint() method to support drawing boxes around the
#     block of code.
##########################################################################
    def paint(self, g):
        text = self.getSelectedText()

        if text != None:
            self.gui.gutter.repaint()

        self.super__paint(g)
        if len(self.indentLines) > 0:
            if self.darkMode:
                g.setColor(LINE_COLOR)
            else:
                g.setColor(awt.Color(215, 215, 253, 127))
            for l in self.indentLines:
                g.drawLine(l[0],l[1],l[0],l[2])
        if self.boxX != 0:
            if self.darkMode:
                g.setColor(awt.Color(77, 79, 89))
            else:
                g.setColor(awt.Color(200, 200, 250))
            g.drawRect(self.boxX - 1, self.boxY, self.boxWidth + 1, self.boxHeight)

        if self.getCaret().getMark() == self.getCaretPosition() and text == None:
            if self.darkMode:
                g.setColor(CURR_LINE_COLOR)
            else:
                g.setColor(awt.Color(0, 0, 0, 10))
            defaultElement = self.document.getDefaultRootElement()
            rowIndex = defaultElement.getElementIndex(self.getCaretPosition())
            rowStart = defaultElement.getElement(rowIndex).getStartOffset()
            model = self.modelToView(rowStart);
            g.fillRect(0, model.y, self.getWidth(), model.height)

        # if self.gui.commandWindow._textpane.caret.visible:
        if not self.focused:
            if self.darkMode:
                g.setColor(awt.Color(0, 0, 0, 70))
            else:
                g.setColor(awt.Color(0, 0, 0, 40))
            g.fillRect(0, 0, self.getWidth(), self.getHeight())


    def docReplaceText(self, offset, strRemoved, strNew):
        self.document.insertString(offset, strNew, None, 0)
        self.document.addUndoEvent(REPLACE_EVENT, offset, strNew, 1, strRemoved)


    def setSelectionEnd(self, selectionEnd):
        self.gui.gutter.repaint()
        self.super__setSelectionEnd(selectionEnd)


    def replaceSelection(self, content):
        self.disableMatchingChar = True
        if self.document.errorLineStart >= 0:
            self.document.removeErrorHighlighting()
        if self.document.highlightLineStart >= 0:
            self.document.removeLineHighlighting()
        self.modified = 1
        self.gui.loadButton.enabled = 1
        self.gui.saveButton.enabled = 1

        selection = self.getSelectedText()
        offset = self.getSelectionStart()
        length = self.getSelectionEnd() - self.getSelectionStart()
        if selection == None:
            if content == '~' and self.document.getLength() == 0:
                # swing.JTextPane.replaceSelection(self, 'def greet(name):\n  print("Hello, " + name + "!")\n  print("Welcome to JES!")')
                str = 'def greet(name):\n  print("Hello, " + name + "!")\n  print("Welcome to JES!")'
                self.document.insertString(offset, str)
            elif content != '':
                self.document.insertString(offset, content)
        else:
            if content == "'":
                self.document.remove(offset, length, 0)
                self.docReplaceText(offset, selection, "'" + selection + "'")
                self.select(offset+1, offset+length+1)
            elif content == '"':
                self.document.remove(offset, length, 0)
                self.docReplaceText(offset, selection, '"' + selection + '"')
                self.select(offset+1, offset+length+1)
            elif content == '[':
                self.document.remove(offset, length, 0)
                self.docReplaceText(offset, selection, '[' + selection + ']')
                self.select(offset+1, offset+length+1)
            elif content == '(':
                self.document.remove(offset, length, 0)
                self.docReplaceText(offset, selection, '(' + selection + ')')
                self.select(offset+1, offset+length+1)
            elif content == '\t':
                doc = self.document
                text = self.getText()
                startPos = self.getSelectionStart()
                endPos = self.getSelectionEnd()
                scan = startPos
                while scan > 0 and text[scan] != '\n':
                    scan -= 1
                if text[scan] == '\n':
                    scan += 1
                textBefore = text[scan:endPos]

                preText = text[scan:startPos]
                if preText.lstrip() == 'def ' and selection == 'methodName':
                    self.select(endPos+1, endPos+1)
                elif preText.lstrip() == 'for ' and selection == 'i':
                    self.select(endPos+10, endPos+10)
                else:
                    doc.insertString(scan, '\t', None, 0)

                    selStart = self.getSelectionStart()
                    selEnd = self.getSelectionEnd()
                    off = selection.count('\n') * 2
                    text = self.getText()
                    i = selStart
                    num = 0;
                    while i < selEnd:
                        if text[i] == '\n':
                            doc.insertString(i + (num*2) + 1, '\t', None, 0)
                            num += 1
                        i += 1
                    self.select(selStart, selEnd + off)
                    text = self.getText()
                    textAfter = text[scan:selEnd + off]
                    self.document.addUndoEvent(REPLACE_EVENT, scan, textAfter, 1, textBefore)
            else:
                self.document.remove(offset, length, 0)
                self.docReplaceText(offset, selection, content)
        self.disableMatchingChar = False
        self.setTitleModified(True)

    def setTitleModified(self, show):
        if self.getText() == self.lastSavedText:
            show = False
            self.modified = 0
            self.gui.saveButton.enabled = 0
        title = self.gui.getTitle()
        if show:
            if title[len(title)-len(MODIFIED_TITLE):] != MODIFIED_TITLE:
                self.gui.setTitle(title + MODIFIED_TITLE)
        else:
            if title[len(title)-len(MODIFIED_TITLE):] == MODIFIED_TITLE:
                self.gui.setTitle(title[:len(title)-len(MODIFIED_TITLE)])


    def focusGained(self, event):
        self.getCaret().visible = True
        if not self.focused:
            self.focused = True
            self.repaint()
            self.gui.gutter.setFocused(True)

    def focusLost(self, event):
        self.getCaret().visible = False
