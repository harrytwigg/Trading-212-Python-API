# -*- coding: utf-8 -*-
"""
Created on Thu May 21 10:28:18 2020

@author: harry

version: 0.0.1
"""


import threading
from pyvirtualdisplay import Display
from datetime import datetime
from re import sub
from time import sleep

import pandas as pd
from bs4 import BeautifulSoup
from splinter import Browser

from colour import *


class API():
    # Sleep tags are sometimes used as otherwise trade execution appears to be disabled for some reason
    
    def __init__(self, apiMode, email, password, updateIntervalRequested=1, isHeadless=False, logging=False):
        # The self keyword references an instance of the class

        self.running = True
        self.logging = logging
        
        apiModeURL = {
            "cfd": "",
            "invest": "https://www.trading212.com/en/login",
            "isa": "https://www.trading212.com/en/login",
        }

        if apiMode == "cfd":
            if self.logging : error("CFD mode not currently supported, aborting")
            self.quit()
        elif apiMode == "invest":
            if self.logging : output("Connecting to Trading 212 " + apiMode)
        elif apiMode == "isa":
            if self.logging : output("Connecting to Trading 212 " + apiMode)
        else:
            if self.logging : error("Invalid API mode, '" + apiMode + "' aborting")
            self.quit()
        
        
        
        self.browser = Browser("firefox", headless=isHeadless)
        self.browser.visit(apiModeURL.get(apiMode))
        self.browser.find_by_id("username-real").fill(email)
        self.browser.find_by_id("pass-real").fill(password)
        self.browser.find_by_value("Log in").first.click()

        self.liveResult = 0.0
        self.freeFunds = 0.0
        self.accountValue = 0.0
        self.portfolioValue = 0.0
        self.openPositions = 0

        looping = True
        while looping:
            try:
                self.browser.find_by_css(
                    'div[class="button-container"]').first.click()
                looping = False
            except:
                sleep(0.05)

        self.getLiveResult()
        self.getFreeFunds()
        self.getAccountValue()
        self.getPortfolioValue()
        self.getOpenPositions()

        # Background update thread
        if updateIntervalRequested == 0:
            if self.logging : output("Parameter updating disabled, manual requests must be used")
        else:
            self.updateInterval = updateIntervalRequested
            self.updateThread = threading.Thread(target=self.update, args=())
            self.updateThread.daemon = True
            self.updateThread.start()
            if self.logging : output("Update interval of " +
                   str(self.updateInterval) + " seconds initialised")

        if self.logging : output("Login successful")

    def getLiveResult(self):
        self.liveResult = float(sub(r'[^\d.]', '', self.browser.find_by_css(
            'span[class="equity-item-value positive"]').first.value))
        return self.liveResult

    def getFreeFunds(self):
        self.freeFunds = float(sub(r'[^\d.]', '', self.browser.find_by_css(
            'span[class="equity-item-value"]').first.value))
        return self.freeFunds

    def getAccountValue(self):
        self.accountValue = float(sub(r'[^\d.]', '', self.browser.find_by_css(
            'span[class="equity-item-value"]').last.value))
        return self.accountValue

    def getPortfolioValue(self):
        self.portfolioValue = self.getAccountValue() - self.getFreeFunds()
        return self.portfolioValue

    def getOpenPositions(self):
        # Gets the initial open positions
        self.getBottomState(1)

        self.soup = BeautifulSoup(self.browser.html, 'html.parser')
        self.tables = self.soup.find_all("table")
        self.table = self.tables[0]

        self.tab_data = [[self.cell.text for self.cell in self.row.find_all(["th", "td"])]
                         for self.row in self.table.find_all("tr")]
        self.df1 = pd.DataFrame(self.tab_data)

        self.table = self.tables[1]
        self.tab_data = [[self.cell.text for self.cell in self.row.find_all(["th", "td"])]
                         for self.row in self.table.find_all("tr")]
        self.df2 = pd.DataFrame(self.tab_data)

        self.df1 = self.df1.drop(self.df1.columns[-1], axis=1)
        self.df2 = self.df2.drop(self.df2.columns[-1], axis=1)
        self.df2 = self.df2.drop(self.df2.columns[-1], axis=1)
        self.columnNames = self.df1.loc[0].tolist()
        self.columnNames[0] = "Ticker"
        self.df2.columns = self.columnNames

        self.df2["Ticker"] = self.df2["Ticker"].str.replace("\n", "")

        self.df2["Quantity"] = self.df2["Quantity"].str.replace("\xa0", "")
        self.df2["Quantity"] = self.df2["Quantity"].astype(float)

        self.df2["Price"] = self.df2["Price"].str.replace("\xa0", "")
        self.df2["Price"] = self.df2["Price"].astype(float)

        self.df2["Current price"] = self.df2["Current price"].str.replace(
            "\n", "")
        self.df2["Current price"] = self.df2["Current price"].str.replace(
            "\xa0", "")
        self.df2["Current price"] = self.df2["Current price"].astype(float)

        self.df2["Market Value"] = self.df2["Market Value"].str.replace(
            "\xa0", "")
        self.df2["Market Value"] = self.df2["Market Value"].astype(float)

        self.df2["Date Created"] = pd.to_datetime(
            self.df2["Date Created"], format="%d.%m.%Y %H:%M:%S")

        self.df2["Result"] = self.df2["Result"].str.replace(
            "\xa0", "")
        self.df2["Result"] = self.df2["Result"].astype(float)

        self.df2["Result (%)"] = self.df2["Result (%)"].str.replace("%", "")
        self.df2["Result (%)"] = self.df2["Result (%)"].str.replace(
            "\xa0", "")
        self.df2["Result (%)"] = self.df2["Result (%)"].astype(float)

        self.openPositions = self.df2
        return self.df2

    def getBottomState(self, desiredState=0):
        # Checks to see if the first second or third tab or none (0) is open along the bottom
        # Then goes to desired state, aka the number of the tab along the botom requested

        self.bottomCurrentState = 0

        try:
            self.browser.find_by_css(
                'span[class="tab-item tabpositions has-tooltip tab-active svg-icon-holder"]').first.value
            self.bottomCurrentState = 1
        except:
            1+1
        try:
            self.browser.find_by_css(
                'span[class="tab-item taborders has-tooltip svg-icon-holder tab-active"]').first.value
            self.bottomCurrentState = 2
        except:
            1+1
        try:
            self.browser.find_by_css(
                'span[class="tab-item tabalarms has-tooltip svg-icon-holder tab-active"]').first.value
            self.bottomCurrentState = 3
        except:
            1+1

        try:
            if self.bottomCurrentState != desiredState:
                if desiredState == 1:
                    self.browser.find_by_css(
                        'span[class="tab-item tabpositions has-tooltip svg-icon-holder"]').first.click()
                elif desiredState == 2:
                    self.browser.find_by_css(
                        'span[class="tab-item taborders has-tooltip svg-icon-holder"]').first.click()
                elif desiredState == 3:
                    self.browser.find_by_css(
                        'span[class="tab-item tabalarms has-tooltip svg-icon-holder"]').first.click()
        except:
            if self.logging : error("Failed to change bottom state from " +
                  self.bottomCurrentState + " to " + desiredState)
            
    def getPrice(self, desiredInstrument=""):
        # Get the unit price of an instrument in £
        
        if desiredInstrument == "":
            if self.logging : error("No instrument requested to get price of")
            return None
        #sleep(0.1)
        self.browser.find_by_id("navigation-search-button").first.click()
        self.browser.find_by_css('input[class="search-input"]').fill(desiredInstrument)
        #sleep(0.5)
        self.browser.find_by_css('div[class="ticker"]').first.click()
        #sleep(0.1)
        self.browser.find_by_css('div[class="buy-button"]').last.click()
        #sleep(0.1)
        self.browser.find_by_css('input[tabindex="-1"]').fill(str(100))
        #sleep(0.1)
        self.unitCost = self.browser.find_by_css('div[class="order-costs deposit-required"]').first.value
        self.unitCost = self.unitCost.replace("~£", "")
        self.unitCost = self.unitCost.replace(" ", "")
        self.unitCost = float(self.unitCost) / 100
        if self.logging : output("The unit cost of " + desiredInstrument + " is £" + str(self.unitCost) + " currently")
        self.browser.find_by_css('div[data-dojo-attach-event="click: close"]').last.click()
        #sleep(0.1)
        self.browser.find_by_css('div[class="close-icon svg-icon-holder"]').first.click()
        #sleep(0.1)
        self.browser.find_by_css('div[class="back-button svg-icon-holder"]').first.click()
        #sleep(0.1)
        return self.unitCost
    
    def buy(self, desiredInstrument="", poundValue=0.0, numberOfShares=0.0):
        # If have already placed a lot of trades ina day, further execution can be temporarily disabled
        
        self.canBuy = True
        self.isPurchased = False
        if desiredInstrument == "":
            if self.logging : error("No instrument requested to buy")
            self.canBuy = False
        if poundValue == 0.0 and numberOfShares == 0.0:
            if self.logging : error("No £ value and no number of shares requested")
            self.canBuy = False
        if not(poundValue == 0.0) and not(numberOfShares == 0.0):
            if self.logging : error("£ value and number of shares cannot both be specified")
            self.canBuy = False
        if self.canBuy:
            #sleep(0.1)
            self.browser.find_by_id("navigation-search-button").first.click()
            self.browser.find_by_css(
                'input[class="search-input"]').fill(desiredInstrument)
            sleep(0.4)
            self.browser.find_by_css(
                'div[class="ticker"]').first.click()
            sleep(0.1)
            self.browser.find_by_css('div[class="buy-button"]').last.click()
            sleep(0.1)

            if poundValue == 0.0:
                self.browser.find_by_css(
                    'input[tabindex="-1"]').fill(str(numberOfShares))
                sleep(0.1)
                self.browser.find_by_css(
                    'div[class="custom-button review-order-button"]').first.click()
                sleep(0.2)
                try:
                    self.browser.find_by_css(
                        'div[class="custom-button review-order-button"]').first.click()
                except:
                    1+1
                sleep(0.1)
                self.browser.find_by_css(
                    'div[class="custom-button send-order-button"]').first.click()
                sleep(0.1)
                self.browser.find_by_css(
                    'div[class="close-icon svg-icon-holder"]').first.click()
                sleep(0.1)
                self.browser.find_by_css(
                    'div[class="back-button svg-icon-holder"]').first.click()
                if self.logging : output("Order to buy " + str(numberOfShares) + " of " + desiredInstrument +
                       " successfully sent Trading 212, wait for confirmation of execution")
                sleep(0.1)
                return 1
            if numberOfShares == 0.0:
                if self.logging : error("Order execution by £ value not currently supported, exiting")
        else:
            return None
    
    def makeDeposit(self, amount=1):
        # Make a deposit using a debit card
        # Uses the first saved card on the account
        # Whole numbers only, else rounded
        
        self.browser.find_by_css('div[class="nav-button real_item deposit-funds-button"]').first.click()
        sleep(5)
        self.browser.find_by_css('input[class="p21m3n7s-input"]').fill(str(round(amount)))
        self.browser.find_by_css('div[class="p21m3n7s-checkbox-icon-wrapper"]').first.click()
        self.browser.find_by_css('div[class="p21m3n7s-label"]').first.click()
        sleep(0.1)
        self.browser.find_by_css('div[class="p21m3n7s-saved-card-item"]').first.click()
        sleep(2)
        self.browser.find_by_css('div[class="p21m3n7s-button p21m3n7s-accent-button"]').first.click()
        sleep(7.5)
        self.browser.find_by_css('div[class="p21m3n7s-label"]').first.click()
        
        if self.logging : output("Deposit successfully made to the account of £" + str(round(amount)))
    
    def getWatchlists(self):
        # Returns a list of the current watchlists and their positions
        self.watchlists = []
        for watchlist in self.browser.find_by_css('div[class="short-title"]'):
            self.watchlists.append(watchlist.text)
        print(self.watchlists)
        
    def update(self):
        # The background update thread
        while self.running:
            self.getLiveResult()
            self.getFreeFunds()
            self.getAccountValue()
            self.getPortfolioValue()
            # self.getOpenPositions()

            sleep(self.updateInterval)

    def quit(self):
        self.running = False
        self.browser.quit()
        if self.logging : output("Browser quit successfully, remember to delete the variable instance")

api = API("isa", "harrytwigg111@gmail.com", "Chicken101", isHeadless=False, logging=True, updateIntervalRequested=0)

api.getWatchlists()
#api.makeDeposit(2.5)
#api.getPrice("GILI")
#api.getPrice("TSLA")
#api.buy(desiredInstrument="GILI", numberOfShares=0.002)
#api.buy(desiredInstrument="TSLA", numberOfShares=0.001)
#for time in range(0, 2):
#    api.buy(desiredInstrument="LK", numberOfShares=0.01)