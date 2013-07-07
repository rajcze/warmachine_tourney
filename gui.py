import sys, os
from PySide import QtCore, QtGui

import cPickle as pickle

from GUI import ui_mainwindow as ui_mw
from controller import Player, Tournament

class PMainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)

        self.ui = ui_mw.Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.changes_to_save = False
        
        self.tournament = Tournament()
        self.ui.t_players.setRowCount(0)
        self.ui.t_pairings.setRowCount(0)
        
        #Set edit box sizes
        metrics = QtGui.QFontMetrics(self.ui.e_pAuid.font())
        self.ui.e_pAuid.setFixedSize(metrics.width("8888"), self.ui.e_pAuid.height())
        self.ui.e_pBuid.setFixedSize(metrics.width("8888"), self.ui.e_pBuid.height())
        metrics = QtGui.QFontMetrics(self.ui.e_pAtp.font())
        self.ui.e_pAtp.setFixedSize(metrics.width("8888"), self.ui.e_pAtp.height())
        self.ui.e_pBtp.setFixedSize(metrics.width("8888"), self.ui.e_pBtp.height())
        self.ui.e_pAcp.setFixedSize(metrics.width("8888"), self.ui.e_pAcp.height())
        self.ui.e_pBcp.setFixedSize(metrics.width("8888"), self.ui.e_pBcp.height())
        self.ui.e_pAkp.setFixedSize(metrics.width("888888"), self.ui.e_pAkp.height())
        self.ui.e_pBkp.setFixedSize(metrics.width("888888"), self.ui.e_pBkp.height())

    def closeEvent(self, event):
        if self.changes_to_save:
            if self.yes_no_dialog("Unsaved changes", "There are unsaved changes. Do you want to save the tournament state before exitting?"):
                self.on_actionSave_tournament_state_triggered(True)
        
        event.accept()

    def __guiclear(self):
        self.ui.t_players.clearContents()
        self.ui.t_players.setRowCount(0)
        self.ui.t_pairings.clearContents()
        self.ui.t_pairings.setRowCount(0)
        self.ui.c_pairRound.clear()
        self.ui.b_addPlayer.setEnabled(True)

    def yes_no_dialog(self, title, question):
        flags = QtGui.QMessageBox.StandardButton.Yes 
        flags |= QtGui.QMessageBox.StandardButton.No
        response = QtGui.QMessageBox.question(self, title,
                                              question,
                                              flags)
        if response == QtGui.QMessageBox.Yes:
            return True
        
        return False

    # ============ TAB PLAYERS ============
    
    def __t_players_fill_row(self, rown, player):
        self.ui.t_players.setItem(rown, 0, QtGui.QTableWidgetItem("%s" % player.uid))
        self.ui.t_players.setItem(rown, 1, QtGui.QTableWidgetItem("%s" % player.name))
        self.ui.t_players.setItem(rown, 2, QtGui.QTableWidgetItem("%s" % player.faction))
        self.ui.t_players.setItem(rown, 3, QtGui.QTableWidgetItem("%s" % player.team))
        self.ui.t_players.setItem(rown, 4, QtGui.QTableWidgetItem("%s" % player.country))
        self.ui.t_players.setItem(rown, 5, QtGui.QTableWidgetItem("%s" % player.tp))
        self.ui.t_players.setItem(rown, 6, QtGui.QTableWidgetItem("%s" % player.sos))
        self.ui.t_players.setItem(rown, 7, QtGui.QTableWidgetItem("%s" % player.cp))
        self.ui.t_players.setItem(rown, 8, QtGui.QTableWidgetItem("%s" % player.kp))
        for column in range(self.ui.t_players.columnCount() - 1):
            self.ui.t_players.resizeColumnToContents(column)
    
    def __t_players_sort_tournament_order(self):
        for column in [8,7,6,5]:
            self.ui.t_players.sortItems(column, QtCore.Qt.SortOrder.DescendingOrder)
    
    def t_players_add_player(self, player):
        rown = self.ui.t_players.rowCount()
        self.ui.t_players.insertRow(rown)
        self.__t_players_fill_row(rown, player)

    def update_t_players_from_tournament(self):
        self.ui.t_players.clearContents()
        self.ui.t_players.setRowCount(0)
        for uid, p in self.tournament.players.iteritems():
            self.t_players_add_player(p)        
        self.__t_players_sort_tournament_order()

    # ------------ Add Player ------------
    
    @QtCore.Slot()
    def on_b_addPlayer_clicked(self):
        name = self.ui.e_name.text()
        faction = self.ui.c_faction.currentText()
        team = self.ui.e_team.text()
        country = self.ui.e_country.text()
        
        uid = self.ui.t_players.rowCount()+1
        p = Player(name, faction, team, country, uid = uid)
        self.tournament.add_player(p)
        self.t_players_add_player(p)
        
        self.tournament.tables = len(self.tournament.players) / 2
        
        # Mark that there are changes to be saved
        self.changes_to_save = True
    
    # ------------ Edit Player ------------    
    
    def __editplayer_guiclear(self):
        self.ui.e_name_2.setText("")
        self.ui.e_team_2.setText("")
        self.ui.e_country_2.setText("")

    @QtCore.Slot(str)
    def on_e_pUid_textEdited(self, text):
        try:
            p = self.tournament.players[text]
        except KeyError:
            self.__editplayer_guiclear()
            return
            
        self.ui.e_name_2.setText(p.name)
        index = self.ui.c_faction_2.findText("%s" % p.factions[0])
        self.ui.c_faction_2.setCurrentIndex(index)
        self.ui.e_team_2.setText(p.team)
        self.ui.e_country_2.setText(p.country)

    @QtCore.Slot()
    def on_b_editPlayer_clicked(self):
        try:
            p = self.tournament.players[self.ui.e_pUid.text()]
        except KeyError:
            QtGui.QMessageBox.warning(self, "Failure", "Player with ID %s does not exist." % self.ui.e_pUid.text())
            return
        
        name = self.ui.e_name_2.text()
        faction = self.ui.c_faction_2.currentText()
        team = self.ui.e_team_2.text()
        country = self.ui.e_country_2.text()

        if not name:
            QtGui.QMessageBox.warning(self, "Failure", "Name must be filled.")
            return
        
        if not self.yes_no_dialog("Save changes", "Are you sure?"):
            return
        
        p.name = name
        p.factions[0] = faction
        p.team = team
        p.country = country
        
        rown = 0
        for rown in range(self.ui.t_players.rowCount()):
            if  self.ui.t_players.item(rown, 0).text() == p.uid:
                break
        self.__t_players_fill_row(rown, p)
        
        self.ui.e_pUid.setText("")
        self.__editplayer_guiclear()
        self._show_pairings(self.tournament.pairings[-1], self.tournament.byes[-1])
        
        # Mark that there are changes to be saved
        self.changes_to_save = True
        

    # ============ TAB PAIRINGS ============

    def _show_pairings(self, pairings, bye):
        tp = self.ui.t_pairings 
        tp.clearContents()
        tp.setRowCount(0)
        
        it = QtGui.QTableWidgetItem
        
        if bye is not None:
            rown = 0
            tp.insertRow(0)            
            tp.setItem(rown, 0, it("Bye"))
            tp.setItem(rown, 1, it(str(bye)))
            
        table_numbers = sorted(pairings.keys())
        for t in table_numbers:
            rown = tp.rowCount()
            tp.insertRow(rown)
            tp.setItem(rown, 0, it("%s" % t))
            tp.setItem(rown, 1, it(str(pairings[t][0])))
            tp.setItem(rown, 2, it(str(pairings[t][1])))
        
        for column in range(tp.columnCount() - 1):
            tp.resizeColumnToContents(column)

    @QtCore.Slot()
    def on_b_startNextRound_clicked(self):
        if len(self.tournament.active_players) < 3:
            QtGui.QMessageBox.information(self, "Information", "At least 3 active players are required to start a round.")
            return
        
        if self.tournament.current_round > -1:
            missing_results = []
            for table, pair in self.tournament.pairings[-1].items():
                if (len(pair[0]._tp) != self.tournament.current_round + 1) or (len(pair[1]._tp) != self.tournament.current_round + 1):
                    missing_results.append(table)
            
            if missing_results:
                QtGui.QMessageBox.information(self, "Information", "Results for tables %r are not filled." % missing_results)
                return
        
        
        pairs, bye = self.tournament.create_pairings()
        self._show_pairings(pairs, bye)
        
        r = self.tournament.current_round + 1
        self.ui.c_pairRound.addItem("%s" % r)
        index = self.ui.c_pairRound.findText("%s" % r)
        self.ui.c_pairRound.setCurrentIndex(index)

        self.ui.statusbar.showMessage("Current round: %s" % r)
        self.ui.b_addPlayer.setEnabled(False)
        
        # Mark that there are changes to be saved
        self.changes_to_save = True
    
    # ============ TAB RESULTS ============
    
    def __addResultGuiClear(self):
        self.ui.e_pAuid.setText("")
        self.ui.e_pBuid.setText("")
        self.ui.e_pAname.setText("")
        self.ui.e_pBname.setText("")
        self.ui.e_pAtp.setText("")
        self.ui.e_pBtp.setText("")
        self.ui.e_pAcp.setText("")
        self.ui.e_pBcp.setText("")
        self.ui.e_pAkp.setText("")
        self.ui.e_pBkp.setText("")
        self.ui.c_pAfaction.clear()
        self.ui.c_pBfaction.clear()
    
    @QtCore.Slot(str)
    def on_e_tblnum_textEdited(self, text):
        if text == "":
            self.__addResultGuiClear()
            return
        if self.tournament.current_round < 0:
            return
        
        try:
            pair = self.tournament.pairings[-1][int(text)]
        except KeyError:
            self.__addResultGuiClear()
            return
        
        self.ui.e_pAuid.setText(pair[0].uid)
        self.ui.e_pBuid.setText(pair[1].uid)
        self.ui.e_pAname.setText(pair[0].name)
        self.ui.e_pBname.setText(pair[1].name)
        
        self.ui.c_pAfaction.clear()
        self.ui.c_pBfaction.clear()
        for faction in pair[0].factions:
            self.ui.c_pAfaction.addItem(faction)
        for faction in pair[1].factions:
            self.ui.c_pBfaction.addItem(faction)

        # if the players already played, prefill also the tp/cp/kp/...
        if len(pair[0]._tp) == (self.tournament.current_round + 1):
            self.ui.e_pAtp.setText(str(pair[0]._tp[-1]))
            self.ui.e_pBtp.setText(str(pair[1]._tp[-1]))
            self.ui.e_pAcp.setText(str(pair[0]._cp[-1]))
            self.ui.e_pBcp.setText(str(pair[1]._cp[-1]))
            self.ui.e_pAkp.setText(str(pair[0]._kp[-1]))
            self.ui.e_pBkp.setText(str(pair[1]._kp[-1]))
            index = self.ui.c_pAfaction.findText(pair[1].factions_played[-1])
            self.ui.c_pAfaction.setCurrentIndex(index)
            index = self.ui.c_pBfaction.findText(pair[0].factions_played[-1])
            self.ui.c_pBfaction.setCurrentIndex(index)
    
    @QtCore.Slot()
    def on_b_saveResult_clicked(self):
        pAuid = self.ui.e_pAuid.text()
        pBuid = self.ui.e_pBuid.text()
        table = self.ui.e_tblnum.text()
        
        if not (table and pAuid and pBuid):
            print "Fill table number"
            return
            
        table = int(table)
        
        pA = self.tournament.players[pAuid]
        pB = self.tournament.players[pBuid]
        
        cround = self.tournament.current_round
        
        if (pA.tables_played[cround] != table) or (pB.tables_played[cround] != table):
            QtGui.QMessageBox.critical(self, "Critical error", "These players did not play on table %s in round %s" % (table, cround + 1))
            return
        
        pAtp = self.ui.e_pAtp.text()
        pAcp = self.ui.e_pAcp.text()
        pAkp = self.ui.e_pAkp.text()
        pBtp = self.ui.e_pBtp.text()
        pBcp = self.ui.e_pBcp.text()
        pBkp = self.ui.e_pBkp.text()
        
        if not (pAtp and pAcp and pAkp and pBtp and pBcp and pBkp):
            QtGui.QMessageBox.information(self, "Information", "You need to fill all the results")
            return
        
        #editing the results
        if len(pA._tp) == cround + 1:        
            if not self.yes_no_dialog("Edit Results", "You are changing once filled results. Are you sure?"):
                return
            pA._tp[-1] = int(pAtp)
            pA._cp[-1] = int(pAcp)
            pA._kp[-1] = int(pAkp)
            pA.factions_played[-1] = self.ui.c_pBfaction.currentText()
            pB._tp[-1] = int(pBtp)
            pB._cp[-1] = int(pBcp)
            pB._kp[-1] = int(pBkp)
            pB.factions_played[-1] = self.ui.c_pAfaction.currentText()
            
        else: #adding new results
            pA._tp.append(int(pAtp))
            pA._cp.append(int(pAcp))
            pA._kp.append(int(pAkp))
            pA.factions_played.append(self.ui.c_pBfaction.currentText())
            pB._tp.append(int(pBtp))
            pB._cp.append(int(pBcp))
            pB._kp.append(int(pBkp))
            pB.factions_played.append(self.ui.c_pAfaction.currentText())
        
        self.update_t_players_from_tournament()
        self.__addResultGuiClear()
        self.ui.e_tblnum.setText("")
        
        # Mark that there are changes to be saved
        self.changes_to_save = True

    # ============ FILE MENU ============

    @QtCore.Slot(bool)
    def on_actionLoad_Players_triggered(self, state):
        if  not self.yes_no_dialog("Load players?", "This will reset the tournament state. Continue?"):
            return
    
        import csv_worker

        self.tournament.clear()
        self.__guiclear()
        for p in csv_worker.read_players():
            uid = self.ui.t_players.rowCount()+1
            p = Player(uid = uid, **p)
            self.tournament.add_player(p)
            self.t_players_add_player(p)
        
        self.tournament.tables = len(self.tournament.players) / 2
        
        # Mark that there are changes to be saved
        self.changes_to_save = True


    @QtCore.Slot(bool)
    def on_actionSave_tournament_state_triggered(self, state):
        #FIXME: add save file dialog
        pickle.dump( self.tournament, open( "save.p", "wb" ) )
        self.changes_to_save = False

    @QtCore.Slot(bool)
    def on_actionLoad_tournament_state_triggered(self, state):
        #FIXME: add load file dialog
        self.tournament = pickle.load( open( "save.p", "rb" ) )
        
        # fill players table
        self.__guiclear()
        for p_uid in sorted(self.tournament.players.keys()):
            self.t_players_add_player(self.tournament.players[p_uid])
        
        # sort them according to Masters 2013
        self.__t_players_sort_tournament_order()
        
        # fill current pairing table
        for i in range(self.tournament.current_round +1):
            self.ui.c_pairRound.addItem("%s" % (i+1))
            index = self.ui.c_pairRound.findText("%s" % (i+1))
            self.ui.c_pairRound.setCurrentIndex(index)
        
        self._show_pairings(self.tournament.pairings[-1], self.tournament.byes[-1])
        
        # update status bar
        self.ui.statusbar.showMessage("Current round: %s" % (self.tournament.current_round + 1))
        
        if self.tournament.current_round > -1:
            self.ui.b_addPlayer.setEnabled(False)
        
        self.changes_to_save = False
        

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    main_window = PMainWindow()
    main_window.show()
    sys.exit(app.exec_())
