"""
/***************************************************************************
 *   copyright (C) 2018 by Marco Caserta                                   *
 *   marco dot caserta at ie dot edu                                       *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
 ***************************************************************************/

 Algorithm for the simulation of Entrepreneurship survival model (Maud and
 Jose)

 Author: Marco Caserta (marco dot caserta at ie dot edu)
 Started : 20.02.2018
 Ended   :

 Execute with: 
 > python model.py

 Modifications:
 04.06.18
    i. group I enters at the end of the first period, i.e., beginning of 2nd
    ii. cumulative nr. of survivors, rather than %

"""

import random
import sys
import numpy as np
import pandas as pd
import csv


# fixed parameters
#  deltaE = 0.8  #  underestimating for experienced
#  deltaN = 1.2 # overestimating for inexperienced
varE   = 0.05 #note that these are stdev !!!
varN   = 0.10
varSE  = 0.02
varSN  = 0.1

class Entrepreneur:
    """
    Basic data structure for management of each player.
    """

    def __init__(self, experience, delta, var, varS, p0, s0):
        self.experience = experience
        self.p = max(delta*p0 + random.gauss(0, var), 0.0)
        self.s = s0 + random.gauss(0, varS)
        self.decision = 0
        #  print("New with p = ", self.p, " and s = ", self.s)

    def makeDecision(self, threshold):
        """
        Decide whether to enter/persist depending on the comparison between the
        individual p and the threshold value.
        """

        if self.p > threshold:
            self.decision = 1
        else:
            self.decision = 0


    def updateBelief(self, alpha, pBayes):
        """
        Update p, i.e., the individual probability.
        """
        self.p = alpha*self.p  + (1.0-alpha)*pBayes

    def updateExperience(self, correction):
        """
        The deltaN value tends to get closer to deltaE over time. This is
        equivalent to modifying the individual probabilities of the
        inexperienced, to get closed to the expected value of the experienced.
        """

        self.p = correction*self.p



def getBayes(t, popT, pop, group, nTot):
    """
    Update rule for individual probabilities.
    At the end of each period, surving players update their own beliefs, based
    on a known rule. Here we are currently using a king of Bayes rule, which
    observes the probability of success in the last period.
    """

    # note: the "or" case was added to deal with the 1-period delay of I
    if t == 0 or (t == 1 and group == 0):
        if getTotal(popT[t], group) == 0:
            return 0
        else:
            return getTotal(pop, group)/getTotal(popT[t], group)
        #  return getTotal(popT[t], group)/nTot
    else:
        if getTotal(popT[t-1], group) == 0:
            return 0
        else:
            return getTotal(popT[t], group)/getTotal(popT[t-1], group)


def getTotal(pop, experience):
    """
    Return the total number of players in a group in a given period.
    """

    return sum([pop[i].experience == experience for i in range(len(pop))])

def getAvgP(pop, group):
    """
    Return the average of the individual probabilities for a given group.
    """

    return np.mean([pop[i].p for i in range(len(pop)) if pop[i].experience ==
    group])

def step(pop, p0):
    """
    One step over time, from t to t+1.
    We apply a "shock", i.e., each individual in the population has a
    probability of surviving equal to p0.
    """
    #  print("\n Moving by one period ... with p0 = ", p0, "\n")
    popNew = []
    for i in range(len(pop)):
        rr = random.random() #  a random in [0.0, 1.0)
        if rr < p0:
            popNew.append(pop[i])

    return popNew

def printStats(pop, t, nE, nN):
    """ 
    Print statistics of current population.
    """

    print("Summary STATS period {0:3d} : ".format(t))
    print("Tot In       = ", len(pop))
    print("    %        = ", len(pop)/(nE + nN))
    print("Subtot E     = ", getTotal(pop, 1))
    print("Subtot N     = ", getTotal(pop, 0))
    print("Avg pi E     = {0:5.2f}".format(getAvgP(pop,1)))
    print("Avg pi N     = {0:5.2f}".format(getAvgP(pop,0)))


def runSim(nESet, nNSet, alpha, nPeriods, deltaE_base, deltaN_base,ff,
pThreshold, pNewE, pNewI):

    #  nESet = [1000]
    #  ratioEvsN = [0.5, 0.8, 0.9, 1.0, 1.1, 1.2, 1.5]


    # write the headers of the csv file
    frow= []
    frow.append("nrE")
    frow.append("nrI")
    frow.append("p0")
    frow.append("S0")

    frow.append("nrE")
    frow.append("nrI")
    frow.append("avgp0_E")
    frow.append("avgp0_I")
     
    for t in range(nPeriods):
        frow.append("nr_E_" + str(t+1))
        frow.append("nr_I_" + str(t+1))
        frow.append("avgp0_E_" + str(t+1))
        frow.append("avgp0_I_" + str(t+1))
        
        frow.append("bayesE_" + str(t+1))
        frow.append("bayesI_" + str(t+1))

        frow.append("nrE_" + str(t+1))
        frow.append("nrI_" + str(t+1))
        frow.append("avgp0_E_" + str(t+1))
        frow.append("avgp0_I_" + str(t+1))
     
    frow.append("nE")
    frow.append("nI")

    allRows = []  #  this is used to write the csv file
    allRows.append(frow)
    dfEl = []

    x = np.arange(0.025, 0.27, 0.025)
    vals = np.sqrt(x)
    unitProgress = ff.max/(nPeriods*len(nNSet)*len(vals))

    for nE in nESet:

        for nN in nNSet:
            #  vals    = np.arange(0.05, 0.55, 0.05)  #  range values for p0
            #  x = np.arange(0.025, 0.27, 0.025)
            #  vals = np.sqrt(x)
            #  vals    = [0.1]
            results = [] # keep track of the percentage of persistent

            for p0 in vals:  #  for every value of the objective probability p0
                if p0 <= pThreshold: #  rare event
                    deltaE = deltaE_base
                    deltaN = deltaN_base
                else:
                    deltaE = deltaN_base
                    deltaN = deltaE_base

                gamma = abs(deltaE-deltaN)/nPeriods

                frow = []

                #  s0 = deltaE*p0
                s0 = min(deltaE, deltaN)*p0

                # frow is used to store information of a row of the csv file
                frow.append(nE)
                frow.append(nN)
                frow.append(p0)
                frow.append(s0)

                popT = [] #  total polation (over all the periods)
                pop = [] #  population of the current period
                # step 0 : Generate initial population
                for i in range(nE):
                    entr = Entrepreneur(1, deltaE, varE, varSE, p0, s0)
                    entr.makeDecision(entr.s)
                    if entr.decision == 1:
                        pop.append(entr)

                for i in range(nN):
                    entr = Entrepreneur(0, deltaN, varN, varSN, p0, s0)
                    entr.makeDecision(entr.s)
                    entr.decision = 0
                    if entr.decision == 1:
                        pop.append(entr)

                popT.append(pop)
                #  printStats(popT[0], 0, nE, nN)

                frow.append(getTotal(pop,1))
                frow.append(getTotal(pop,0))
                frow.append(getAvgP(pop,1))
                frow.append(getAvgP(pop,0))


                # cycle over all the periods
                for t in range(nPeriods):

                    pop = step(popT[t], p0)


                    #  printStats(pop, t+1, nE, nN)

                    frow.append(getTotal(pop,1))
                    frow.append(getTotal(pop,0))
                    frow.append(getAvgP(pop,1))
                    frow.append(getAvgP(pop,0))

                    # update experience: deltaN tends to deltaE
                    if deltaE < deltaN:
                        correction = 1.0/(1.0+gamma)
                    else:
                        correction = 1.0+gamma

                    for i in range(len(pop)):
                        if pop[i].experience == 0:
                            pop[i].updateExperience(correction)

                    # update beliefs
                    bayesE = getBayes(t, popT, pop, 1, nE)
                    bayesN = getBayes(t, popT, pop, 0, nN)
                    #  print("Bayes Beliefs :: E = {0:5.2f}, N = {1:5.2f}".format(bayesE,
                    #  bayesN))
                    frow.append(bayesE)
                    frow.append(bayesN)
                    for i in range(len(pop)):
                        if pop[i].experience == 1:
                            pBayes = bayesE
                        else:
                            pBayes = bayesN
                        pop[i].updateBelief(alpha, pBayes)

                    #  print("After Bayes update beliefs we get :: ")
                    #  printStats(pop, t+1, nE, nN)

                    # each individual persists depending on the updated beliefs
                    popAux = []
                    for i in range(len(pop)):
                        pop[i].makeDecision(pop[i].s)
                        if pop[i].decision == 1:
                            popAux.append(pop[i])

                    # add new entrants at the end of the period(beginning of
                    # previous period)


                    if t < nPeriods-1:
                        newE = int(pNewE*getTotal(pop,1))
                        avgP_E = getAvgP(popAux,1)
                        print("NEW ENTRANTS E :", newE)
                        #  print("  Parameters :  p0 = {0:5.2f}, s0 = {1:5.2f}".format(avgP_E, s0))
                        for i in range(newE):
                            entr = Entrepreneur(1, 1.0, varE, varSE, avgP_E, s0)
                            entr.makeDecision(entr.s)
                            if entr.decision == 1:
                                popAux.append(entr)

                        newN = int(pNewI*getTotal(pop,0))
                        avgP_N = getAvgP(popAux,0)
                        print("NEW ENTRANTS N :", newN)
                        #  print("  Parameters :  p0 = {0:5.2f}, s0 = {1:5.2f}".format(avgP_N, s0))
                        if t > 0:
                            for i in range(newN):
                                entr = Entrepreneur(0, 1.0, varN, varSN, avgP_N, s0)
                                entr.makeDecision(entr.s)
                                if entr.decision == 1:
                                    popAux.append(entr)


                    # first, let us add the inexperienced if it is first period
                    if t == 0:
                        for i in range(nN):
                            entr = Entrepreneur(0, deltaN, varN, varSN, p0, s0)
                            entr.makeDecision(entr.s)
                            if entr.decision == 1:
                                popAux.append(entr)

                    popT.append(popAux)

                    frow.append(getTotal(popT[t+1],1))
                    frow.append(getTotal(popT[t+1],0))
                    frow.append(getAvgP(popT[t+1],1))
                    frow.append(getAvgP(popT[t+1],0))

                    #  input("End of period ")
                    # update progress widget
                    ff.value += unitProgress

                # store results of this iteration
                results.append([p0, getTotal(popT[nPeriods], 1),
                getTotal(popT[nPeriods], 0)])
                frow.append(getTotal(popT[nPeriods], 1))
                frow.append(getTotal(popT[nPeriods], 0))
                allRows.append(frow)
                
                dfEl.append({"nrE":frow[0], "nrI":frow[1], "p0":p0, "nE":frow[-2],
                "nI":frow[-1]})


        csvfile = "summary_" + str(nPeriods) + ".csv"
        output = open(csvfile, "w")
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(allRows)

        df = pd.DataFrame(dfEl)

        return df

def runSimTime(nESet, nNSet, alpha, nPeriods, deltaE_base, deltaN_base,ff, p0L,
p0H, pThreshold, pNewE, pNewI):

    # write the headers of the csv file
    frow= []
    frow.append("nrE")
    frow.append("nrI")
    frow.append("p0")
    frow.append("S0")

    frow.append("nrE")
    frow.append("nrI")
    frow.append("avgp0_E")
    frow.append("avgp0_I")
     
    for t in range(nPeriods):
        frow.append("nr_E_" + str(t+1))
        frow.append("nr_I_" + str(t+1))
        frow.append("avgp0_E_" + str(t+1))
        frow.append("avgp0_I_" + str(t+1))
        
        frow.append("bayesE_" + str(t+1))
        frow.append("bayesI_" + str(t+1))

        frow.append("nrE_" + str(t+1))
        frow.append("nrI_" + str(t+1))
        frow.append("avgp0_E_" + str(t+1))
        frow.append("avgp0_I_" + str(t+1))
     
    frow.append("nE")
    frow.append("nI")

    allRows = []  #  this is used to write the csv file
    allRows.append(frow)
    dfEl = []
    dfTime = []

    vals = [p0L, p0H]
    unitProgress = ff.max/(nPeriods*len(nNSet)*len(vals))

    for nE in nESet:

        for nN in nNSet:
            results = [] # keep track of the percentage of persistent

            for p0 in vals:  #  for every value of the objective probability p0
                if p0 <= pThreshold: #  rare event
                    deltaE = deltaE_base
                    deltaN = deltaN_base
                else:
                    deltaE = deltaN_base
                    deltaN = deltaE_base

                gamma = abs(deltaE-deltaN)/nPeriods

                frow = []

                #  s0 = deltaE*p0
                s0 = min(deltaE, deltaN)*p0

                # frow is used to store information of a row of the csv file
                frow.append(nE)
                frow.append(nN)
                frow.append(p0)
                frow.append(s0)

                popT = [] #  total polation (over all the periods)
                pop = [] #  population of the current period
                # step 0 : Generate initial population
                for i in range(nE):
                    entr = Entrepreneur(1, deltaE, varE, varSE, p0, s0)
                    entr.makeDecision(entr.s)
                    if entr.decision == 1:
                        pop.append(entr)

                for i in range(nN):
                    entr = Entrepreneur(0, deltaN, varN, varSN, p0, s0)
                    entr.makeDecision(entr.s)
                    entr.decision = 0
                    if entr.decision == 1:
                        pop.append(entr)

                popT.append(pop)
                #  printStats(popT[0], 0, nE, nN)

                frow.append(getTotal(pop,1))
                frow.append(getTotal(pop,0))
                frow.append(getAvgP(pop,1))
                frow.append(getAvgP(pop,0))


                # cycle over all the periods
                for t in range(nPeriods):

                    pop = step(popT[t], p0)


                    #  printStats(pop, t+1, nE, nN)

                    frow.append(getTotal(pop,1))
                    frow.append(getTotal(pop,0))
                    frow.append(getAvgP(pop,1))
                    frow.append(getAvgP(pop,0))

                    # update experience: deltaN tends to deltaE
                    if deltaE < deltaN:
                        correction = 1.0/(1.0+gamma)
                    else:
                        correction = 1.0+gamma

                    for i in range(len(pop)):
                        if pop[i].experience == 0:
                            pop[i].updateExperience(correction)

                    # update beliefs
                    bayesE = getBayes(t, popT, pop, 1, nE)
                    bayesN = getBayes(t, popT, pop, 0, nN)
                    #  print("Bayes Beliefs :: E = {0:5.2f}, N = {1:5.2f}".format(bayesE,
                    #  bayesN))
                    frow.append(bayesE)
                    frow.append(bayesN)
                    for i in range(len(pop)):
                        if pop[i].experience == 1:
                            pBayes = bayesE
                        else:
                            pBayes = bayesN
                        pop[i].updateBelief(alpha, pBayes)

                    #  print("After Bayes update beliefs we get :: ")
                    #  printStats(pop, t+1, nE, nN)

                    # each individual persists depending on the updated beliefs
                    popAux = []
                    for i in range(len(pop)):
                        pop[i].makeDecision(pop[i].s)
                        if pop[i].decision == 1:
                            popAux.append(pop[i])

                    # add new entrants at the end of the period(beginning of
                    # previous period)


                    if t < nPeriods-1:
                        newE = int(pNewE*getTotal(pop,1))
                        avgP_E = getAvgP(popAux,1)
                        #  print("NEW ENTRANTS E :", newE)
                        #  print("  Parameters :  p0 = {0:5.2f}, s0 = {1:5.2f}".format(avgP_E, s0))
                        for i in range(newE):
                            entr = Entrepreneur(1, 1.0, varE, varSE, avgP_E, s0)
                            entr.makeDecision(entr.s)
                            if entr.decision == 1:
                                popAux.append(entr)

                        newN = int(pNewI*getTotal(pop,0))
                        avgP_N = getAvgP(popAux,0)
                        #  print("NEW ENTRANTS N :", newN)
                        #  print("  Parameters :  p0 = {0:5.2f}, s0 = {1:5.2f}".format(avgP_N, s0))
                        if t > 0:
                            for i in range(newN):
                                entr = Entrepreneur(0, 1.0, varN, varSN, avgP_N, s0)
                                entr.makeDecision(entr.s)
                                if entr.decision == 1:
                                    popAux.append(entr)


                    # first, let us add the inexperienced if it is first period
                    if t == 0:
                        for i in range(nN):
                            entr = Entrepreneur(0, deltaN, varN, varSN, p0, s0)
                            entr.makeDecision(entr.s)
                            if entr.decision == 1:
                                popAux.append(entr)

                    popT.append(popAux)

                    frow.append(getTotal(popT[t+1],1))
                    frow.append(getTotal(popT[t+1],0))
                    frow.append(getAvgP(popT[t+1],1))
                    frow.append(getAvgP(popT[t+1],0))

                    #  input("End of period ")
                    # update progress widget
                    ff.value += unitProgress

                # store results of this iteration
                results.append([p0, getTotal(popT[nPeriods], 1),
                getTotal(popT[nPeriods], 0)])
                frow.append(getTotal(popT[nPeriods], 1))
                frow.append(getTotal(popT[nPeriods], 0))
                allRows.append(frow)
                
                dfEl.append({"nrE":frow[0], "nrI":frow[1], "p0":p0, "nE":frow[-2],
                "nI":frow[-1]})

                pos = 4
                stepsize = 10
                for tt in range(nPeriods+1):
                    dfTime.append({"p0": p0, "nrE": frow[0], "nrI": frow[1],
                    "t": tt, "nE": frow[pos], "nI": frow[pos+1]})
                    pos += stepsize

        csvfile = "summary_" + str(nPeriods) + ".csv"
        output = open(csvfile, "w")
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(allRows)

        df = pd.DataFrame(dfEl)
        dfT= pd.DataFrame(dfTime)

        return dfT

