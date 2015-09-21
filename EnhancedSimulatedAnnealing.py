import math
import random
import numpy
import sys

class EnhancedSA:
    #Temperature stage parameters
    ProbOK = 0.5
    degInit = 0.0
    degCheckTime = 500
    N1 = 12
    N2 = 100

    #Stopping tests parameters
    epsRel = 1.0e-6
    epsAbs = 1.0e-8
    nFMax = 5000
    nNoDown = 0
    stepInit = []
    startEnOpt = 0
    #tips: adjust the following parameters will improve the precision
    #tips: lower, more accurate
    adaTempStop = True
    tempStop = -1.0e-6
    #tips: higher, more accurate
    plainStay = 4

    #Temperature adjustment rule parameters
    RMaxTemp = 0.9
    RMinTemp = 0.1

    #Step vector adjustment rule parameters
    RatioMax = 0.2
    RatioMin = 0.05
    ExtStep = 2
    ShrStep = 0.5
    RoStep = []

    #Moving Counters
    nFObj = 1
    MvOKStep = 0
    aMvOKStep = []
    MvUpStep = 0
    MvAttStep = 0
    aMvAttStep = []

    #Variables
    x = []
    n = -1
    xMin = []
    xMax = []
    step = []
    xOpt = []
    enOpt = 0.0
    oldEn = 0.0
    temp = 0.0
    enLowest = 0.0
    avgEn = 0.0
    avgUpEn = 0.0

    #Space partition statistics
    p = 0
    lessIdx = 0
    idxArray = [[], []]
    moveIndex = []

    def f(self, x):
        pass

    def getDegInit(self):
        ret = 0.0
        tmpEn = self.f(self.x)
        for i in range(self.degCheckTime):
            tmpX = []
            for j in range(self.n):
                tmpX.append(random.uniform(self.xMin[j], self.xMax[j]))
            newEn = self.f(tmpX)
            ret += math.fabs(newEn - tmpEn)
        return ret / self.degCheckTime

    def initialize(self, n, xMin, xMax):
        #Choose
        self.n = n
        self.xMin = xMin
        self.xMax = xMax
        for i in range(self.n):
            center = (self.xMin[i] + self.xMax[i]) / 2.0
            self.x.append(center)
        print('Check: initial x\'s = ' + str(self.x), file = sys.stderr)

        #Compute
        en = self.f(self.x)
        for i in range(self.n):
            self.RoStep.append(0.25)
            length = (self.xMax[i] - self.xMin[i]) * self.RoStep[i]
            self.step.append(length)
            self.stepInit.append(length)
        print('Check: initial steps = ' + str(self.step), file = sys.stderr)

        self.degInit = self.getDegInit()
        print('Check: initial degree = ' + str(self.degInit), file = sys.stderr)

        self.temp = -self.degInit / math.log(self.ProbOK)
        print('Check: initial temperature = ' + str(self.temp), file = sys.stderr)
        if self.adaTempStop:
            self.tempStop = -(self.epsRel ** 2 * self.degInit + self.epsAbs) / math.log(self.epsRel * self.ProbOK + self.epsAbs)
        print('Check: stop temperature = ' + str(self.tempStop), file = sys.stderr)

        #Set
        self.xOpt = self.x
        self.enOpt = en
        self.oldEn = en
        for i in range(self.n):
            self.aMvOKStep.append(0)
            self.aMvAttStep.append(0)
        self.enLowest = en
        
        for i in range(self.n):
            self.idxArray[self.lessIdx].append(i)
        return
        
    def spacePartition(self):
        self.p = random.randint(1, self.n)
        self.moveIndex = []

        if len(self.idxArray[self.lessIdx]) <= self.p:
            self.p = self.p - len(self.idxArray[self.lessIdx])
            self.moveIndex.extend(self.idxArray[self.lessIdx])
            self.idxArray[1 - self.lessIdx].extend(self.idxArray[self.lessIdx])
            self.idxArray[self.lessIdx] = []
            self.lessIdx = 1 - self.lessIdx

        random.shuffle(self.idxArray[self.lessIdx])
        self.moveIndex.extend(self.idxArray[self.lessIdx][:self.p])
        self.idxArray[1 - self.lessIdx].extend(self.idxArray[self.lessIdx][:self.p])
        self.idxArray[self.lessIdx] = self.idxArray[self.lessIdx][self.p:]

        #print('Check: len(ret)=' + str(len(self.moveIndex)) + ' and p=' + str(self.p), file = sys.stderr)
        return

    def accept(self, xTry, newEn):
        self.x = xTry
        self.oldEn = newEn
        for i in range(len(self.moveIndex)):
            self.aMvOKStep[self.moveIndex[i]] += 1
        self.MvOKStep += 1
        return

    def move(self):
        xTry = []
        self.spacePartition()
        for i in range(self.n):
            valInit = self.x[i]
            rand = random.uniform(-1.0, 1.0)
            valNew = valInit
            if i in self.moveIndex:
                valNew = valInit + rand * self.step[i]
            if valNew > self.xMax[i] or valNew < self.xMin[i]:
                valNew = valInit - rand * self.step[i]
            xTry.append(valNew)
            #if val >= self.xMin[i] and val <= self.xMax[i]:
            #    xTry.append(val)
            #elif val < self.xMin[i]:
            #    xTry.append(self.xMin[i] * 2 - val)
            #elif val > self.xMax[i]:
            #    xTry.append(self.xMax[i] * 2 - val)
            #else:
            #    print('Error: Strange value occurred when moving.', file = sys.stderr)
            if xTry[i] > self.xMax[i] or xTry[i] < self.xMin[i]:
                print('Error: Move out of boundaries.' , file = sys.stderr)
                print('--ValInit = ' + str(valInit) + ' , ValNew = ' + str(valNew) + ', Step = ' + str(rand * self.step[i]), file = sys.stderr)
                print('--Rand = ' + str(rand) + ' , perStep = ' + str(self.step[i]), file = sys.stderr)
                input()

        if len(xTry) != self.n:
            print('Error: Dimension loss when moving.', file = sys.stderr)

        newEn = self.f(xTry)
        deltaEn = newEn - self.oldEn
        for i in range(len(self.moveIndex)):
            self.aMvAttStep[self.moveIndex[i]] += 1
        self.nFObj += 1
        self.MvAttStep += 1
        self.avgEn += newEn

        if deltaEn <= 0:
            self.accept(xTry, newEn)            
            if newEn < self.enOpt:
                self.xOpt = xTry
                self.enOpt = newEn
                self.enLowest = newEn
        else:
            prob = math.exp(-deltaEn / self.temp)
            if prob > random.uniform(0.0, 1.0):
                self.accept(xTry, newEn)
                self.MvUpStep += 1
                self.avgUpEn += deltaEn
        return

    def isEndOfTemperatureStage(self):
        if self.MvOKStep < self.N1 * self.n and self.MvAttStep < self.N2 * self.n:
            return False

        if self.startEnOpt - self.enOpt > self.epsRel:
            self.nNoDown = 0
        else:
            self.nNoDown += 1

        if self.nNoDown > 0:
            print('Alert: This temperature stage includes no downhill operation.', file = sys.stderr)

        return True

    def adjustTemperature(self):
        self.avgEn /= self.MvAttStep
        ratio = max(min(self.enLowest / self.avgEn, self.RMaxTemp), self.RMinTemp)
        self.temp *= ratio

    def adjustStepVector(self):
        for i in range(self.n):
            ratioOK = self.aMvOKStep[i] / self.aMvAttStep[i]
            if ratioOK > self.RatioMax:
                self.step[i] *= self.ExtStep
                if self.step[i] > (self.xMax[i] - self.xMin[i]) / 2:
                    self.step[i] /= self.ExtStep
            elif ratioOK < self.RatioMin:
                self.step[i] *= self.ShrStep
        return
    
    def isEndOfAnnealing(self):
        #1: No downhill moves during last 4 temperature stage
        if self.nNoDown > self.plainStay:
            print('Alert: The 1st type of ending.', file = sys.stderr)
            return True
        
        #2: Temperature is low enough
        if self.temp < self.tempStop:
            print('Alert: The 2nd type of ending.', file = sys.stderr)
            return True
        
        #3: Any element in step vector is small enough
        for i in range(self.n):
            if self.step[i] < self.epsRel * self.stepInit[i] + self.epsAbs:
                print('Alert: The 3rd type of ending.', file = sys.stderr)
                return True
        
        #4: The number of moves is big enough
        if self.nFObj >= self.nFMax * self.n:
            print('Alert: The 4th type of ending.', file = sys.stderr)
            return True
        return False

    def initializeNewTemperature(self):
        self.startEnOpt = self.enOpt
        self.MvOKStep = 0
        self.MvUpStep = 0
        self.MvAttStep = 0
        for i in range(self.n):
            self.aMvOKStep[i] = 0
            self.aMvAttStep[i] = 0
        self.enLowest = self.oldEn
        self.avgEn = 0
        self.avgUpEn = 0
        return
    
    def work(self, n, xMin, xMax):
        self.initialize(n, xMin, xMax)
        t = 1
        while not self.isEndOfAnnealing():
            self.initializeNewTemperature()
            while not self.isEndOfTemperatureStage():
                self.move()
            self.adjustTemperature()
            self.adjustStepVector()
            print('Alert: The ' + str(t) + ' times of annealing with energy ' + str(self.enOpt) + '.', file = sys.stderr)
            t = t + 1
        print('Alert: The solution is found out.', file = sys.stderr)
        print('x = ' + str(self.xOpt), file = sys.stdout)
        print('f(x) = ' + str(self.enOpt), file = sys.stdout)
        return

class OptimizeGoldStein(EnhancedSA):
    def f(self, x):
        return (1 + ((x[0] + x[1] + 1) ** 2) * (19 - 14*x[0] + 3*x[0]*x[0] - 14*x[1] + 6*x[0]*x[1]
            + 3*x[1]*x[1])) * (30 + ((2*x[0] - 3*x[1]) ** 2) * (18 - 32*x[0] + 12*x[0]*x[0] +
                48*x[1] - 36*x[0]*x[1] + 27*x[1]*x[1]))

class OptimizeZakharov(EnhancedSA):
    adaTempStop = False 
    plainStay = 50
    nFMax = 2000000

    def f(self, x):
        ret = 0.0
        for i in range(len(x)):
            ret += x[i] ** 2
        tmp = 0.0
        for i in range(len(x)):
            tmp += 0.5 * i * x[i]
        ret += tmp ** 2
        ret += tmp ** 4
        return ret

class OptimizeNaive(EnhancedSA):
    def f(self, x):
        ret = 0.0
        for i in range(len(x)):
            ret += x[i]
        return -math.fabs(ret) 

def test():
    #optimizer = OptimizeGoldStein()
    #print('Ground truth: x = [0, -1], f(x) = ' + str(optimizer.f([0, -1])))
    #optimizer.work(2, [-2, -2], [2, 2])

    optimizer = OptimizeZakharov()
    print('Ground truth: x = [0, .., 0], f(x) = 0')
    N = 100
    xMin = []
    xMax = []
    for i in range(N):
        xMin.append(-500)
        xMax.append(1000)
    optimizer.work(N, xMin, xMax)

    #optimizer = OptimizeNaive()
    #N = 100
    #xMin = []
    #xMax = []
    #for i in range(N):
    #    xMin.append(-5)
    #    xMax.append(10)
    #optimizer.work(N, xMin, xMax)
    

test()
