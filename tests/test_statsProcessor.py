import unittest
from unittest.mock import MagicMock, ANY

from timerecorder.statsProcessor import StatsProcessor
from tests.test_base import TestBase
from timerecorder import config
from builtins import range
from timerecorder.updateScriptHandler import UpdateScriptHandler
import simpleaudio

fieldCount = 66

class TestStatsProcessor(TestBase):

    def mockAwaySideEffects(self):
        simpleaudio.WaveObject = MagicMock()

    def __init__(self, methodName):
        TestBase.__init__(self, methodName, 'test-files')
        self.CleanUpFunction = UpdateScriptHandler.cleanUp
        self.UpdateResourcesFunction = StatsProcessor.updateResources

    def setUp(self):
        UpdateScriptHandler.cleanUp = MagicMock()
        StatsProcessor.updateResources = MagicMock()
        self.thing = StatsProcessor('test.statsProcessor')
        self.thing.logResults = MagicMock()

        self.stats = range(0, 256)
        self.allZeroStats = [0.0] * 256

    def tearDown(self):
        UpdateScriptHandler.cleanUp = self.CleanUpFunction
        StatsProcessor.updateResources = self.UpdateResourcesFunction

    def mockVisitorMethods(self):
        self.thing.resetRecognition = MagicMock()
        self.thing.startStage = MagicMock()
        self.thing.finishStage = MagicMock()

    # Scenario for timeDelta<0 and !restart: 1) cancel DR1 event near the start  2) enter the same event again (similar x/y pos)
    def testStageRestartOrTimeResetLeadToStageAborted(self):
        self.thing.timeTracker.getTimeDelta = MagicMock(return_value=-1)
        self.thing.respawnTracker.isRestart = MagicMock(return_value=False)
        self.assertTrue(self.thing.stageAborted())

        self.thing.timeTracker.getTimeDelta = MagicMock(return_value=1)
        self.thing.respawnTracker.isRestart = MagicMock(return_value=True)
        self.assertTrue(self.thing.stageAborted())

        self.thing.timeTracker.getTimeDelta = MagicMock(return_value=1)
        self.thing.respawnTracker.isRestart = MagicMock(return_value=False)
        self.assertFalse(self.thing.stageAborted())

    def testStartStage(self):
        self.mockVisitorMethods()
        self.thing.handleGameState(False, False, 0, -0.2, self.stats)

        self.assertFalse(self.thing.resetRecognition.called, 'Actually called unexpected receiver method')
        self.assertTrue(self.thing.startStage.called, 'Never called expected receiver method')
        self.assertFalse(self.thing.finishStage.called, 'Actually called unexpected receiver method')

    # This will ultimately lead to a recover to the start line which is treated as Restart (DR2: Disqualify?)
    def testMoveCarBehindStartLineDoesNotBreakRecognition(self):
        self.mockVisitorMethods()
        self.thing.handleGameState(False, True, 0, -0.2, self.stats)

        self.assertFalse(self.thing.resetRecognition.called, 'Actually called unexpected receiver method')
        self.assertFalse(self.thing.startStage.called, 'Actually called unexpected receiver method')
        self.assertFalse(self.thing.finishStage.called, 'Actually called unexpected receiver method')

    def testStatsAfterAStageLeadToResetButNotStartStage(self):
        self.mockVisitorMethods()
        self.thing.handleGameState(True, True, 0, 0.9, self.allZeroStats)

        self.assertTrue(self.thing.resetRecognition.called, 'Never called expected receiver method')
        self.assertFalse(self.thing.startStage.called, 'Actually called unexpected receiver method')
        self.assertFalse(self.thing.finishStage.called, 'Actually called unexpected receiver method')

    def testResetRecognitionWhenStageIsAborted(self):
        self.mockVisitorMethods()
        self.thing.handleGameState(True, False, 0, 0.2, self.stats)

        self.assertTrue(self.thing.resetRecognition.called, 'Never called expected receiver method')
        self.assertFalse(self.thing.startStage.called, 'Actually called unexpected receiver method')
        self.assertFalse(self.thing.finishStage.called, 'Actually called unexpected receiver method')

    def testFinishStage(self):
        self.mockVisitorMethods()
        self.thing.handleGameState(False, True, 1, 0.9, self.stats)

        self.assertTrue(self.thing.resetRecognition.called, 'Actually called unexpected receiver method')
        self.assertFalse(self.thing.startStage.called, 'Actually called unexpected receiver method')
        self.assertTrue(self.thing.finishStage.called, 'Never called expected receiver method')

    def testFinishStageOnlyOnce(self):
        self.mockVisitorMethods()
        self.thing.handleGameState(False, False, 1, 0.9, self.stats)

        self.assertFalse(self.thing.resetRecognition.called, 'Actually called unexpected receiver method')
        self.assertFalse(self.thing.startStage.called, 'Actually called unexpected receiver method')
        self.assertFalse(self.thing.finishStage.called, 'Never called expected receiver method')

    def testFinishStageInDR2TimeTrial(self):
        self.mockVisitorMethods()
        self.thing.handleGameState(False, True, 0, 0.999, self.allZeroStats)

        self.assertTrue(self.thing.resetRecognition.called, 'Actually called unexpected receiver method')
        self.assertFalse(self.thing.startStage.called, 'Actually called unexpected receiver method')
        self.assertTrue(self.thing.finishStage.called, 'Never called expected receiver method')

    def testDontFinishStageInDR2TimeTrialIfNotAtEndOfStage(self):
        self.mockVisitorMethods()
        self.thing.handleGameState(False, True, 0, 0.822, self.allZeroStats)

        self.assertFalse(self.thing.resetRecognition.called, 'Actually called unexpected receiver method')
        self.assertFalse(self.thing.startStage.called, 'Actually called unexpected receiver method')
        self.assertFalse(self.thing.finishStage.called, 'Actually called unexpected receiver method')

    def testTopSpeedConversion(self):
        config.get.speed_unit = 'kph'
        self.thing = StatsProcessor('testroot')
        self.thing.speedTracker.topSpeed = 33.28

        format_top_speed = self.thing.formatTopSpeed()
        self.assertEqual(format_top_speed, '119.8')

        config.get.speed_unit = 'mph'
        self.thing = StatsProcessor('testroot')
        self.thing.speedTracker.topSpeed = 33.28

        format_top_speed = self.thing.formatTopSpeed()
        self.assertEqual(format_top_speed, '74.4')

    def testLapTimeConversion(self):
        format_lap_time = self.thing.formatLapTime(180.249)
        self.assertEqual(format_lap_time, '180.25')

    def testNiceLapTimeConversion(self):
        laptime = self.thing.prettyLapTime(180.240)
        self.assertEqual(str(laptime), '03:00.240')

        laptime = self.thing.prettyLapTime(3612.240)
        self.assertEqual(str(laptime), '1:00:12.240')

    def testHandleFinishStage(self):
        stats = [1] * fieldCount

        self.thing.inStage = MagicMock(return_value=True)
        self.thing.finishStage = MagicMock()

        # stats[59] == 1 means lap/stage complete
        stats[59] = 1
        self.thing.handleStats(stats)

        self.thing.finishStage.assert_called_once()

    def testFinishStageRecordAndLogResultsWithNewPersonalBest(self):
        stats = [1] * fieldCount
        stats[62] = 100.2
        self.thing.databaseAccess = MagicMock()
        self.thing.car = 10
        self.thing.track = 11
        self.thing.handleAmbiguities = MagicMock(return_value=(10, 11))
        self.thing.databaseAccess.recordResults = MagicMock(return_value=(123456789, 111.2))

        self.thing.finishStage(stats)

        self.thing.handleAmbiguities.assert_called_once()
        self.thing.databaseAccess.recordResults.assert_called_once_with(10, 11, ANY, ANY, ANY)
        self.thing.logResults.assert_called_once_with(100.2, 10, 11, 111.2)

    def testFinishStageRecordAndLogResultsWithNoNewPersonalBest(self):
        stats = [1] * fieldCount
        stats[62] = 100.2
        self.thing.databaseAccess = MagicMock()
        self.thing.car = 10
        self.thing.track = 11
        self.thing.handleAmbiguities = MagicMock(return_value=(10, 11))
        self.thing.databaseAccess.recordResults = MagicMock(return_value=None)

        self.thing.finishStage(stats)

        self.thing.handleAmbiguities.assert_called_once()
        self.thing.databaseAccess.recordResults.assert_called_once_with(10, 11, ANY, ANY, ANY)
        self.thing.logResults.assert_called_once_with(100.2, 10, 11)

    def testFinishStageRecordAndLogResultsWithAmbiguity(self):
        stats = [1] * fieldCount
        stats[62] = 100.2
        self.thing.databaseAccess = MagicMock()
        self.thing.car = 10
        self.thing.track = (11, 110)
        self.thing.handleAmbiguities = MagicMock(return_value=(10, 11))
        self.thing.databaseAccess.recordResults = MagicMock(return_value=(123456789, 111.2))

        self.thing.finishStage(stats)

        self.thing.handleAmbiguities.assert_called_once()
        self.thing.databaseAccess.recordResults.assert_called_once_with(10, 11, ANY, ANY, ANY)
        self.thing.logResults.assert_called_once_with(100.2, 10, 11)

    def testHandleStartStageAndDatabaseCalled(self):
        stats = [1] * fieldCount
        stats[2] = 0

        self.thing.inStage = MagicMock(return_value=False)
        self.thing.databaseAccess = MagicMock()
        self.thing.databaseAccess.identifyCar = MagicMock(return_value=10)
        self.thing.databaseAccess.identifyTrack = MagicMock(return_value=11)

        self.thing.handleStats(stats)

        self.thing.databaseAccess.identifyCar.assert_called_once()
        self.thing.databaseAccess.identifyTrack.assert_called_once()
        self.thing.databaseAccess.recordResults.assert_not_called()

    def testTrackersAreCalledWithStats(self):
        self.thing.timeTracker = MagicMock()
        self.thing.stageAborted = MagicMock(return_value=False)

        stats = [1] * fieldCount
        self.thing.handleStats(stats)

        self.thing.timeTracker.track.assert_called()

    def testTrackersAreNotCalledWithEmptyStats(self):
        self.thing.timeTracker = MagicMock()
        self.thing.stageAborted = MagicMock(return_value=False)

        stats = [0] * fieldCount
        self.thing.handleStats(stats)

        self.thing.timeTracker.track.assert_not_called()

    def testCarControlsAreShownIfConfigured(self):
        self.thing.inStage = MagicMock(return_value=False)
        self.thing.databaseAccess = MagicMock()
        self.thing.databaseAccess.identifyCar = MagicMock(return_value=10)
        self.thing.databaseAccess.identifyTrack = MagicMock(return_value=11)

        self.thing.showCarControlInformation = MagicMock()
        stats = [1] * fieldCount

        config.get.show_car_controls = 0
        self.thing.startStage(stats)
        self.thing.showCarControlInformation.assert_not_called()

        config.get.show_car_controls = 1
        self.thing.startStage(stats)
        self.thing.showCarControlInformation.assert_called_once()

    def testLogTrack(self):
        self.thing.database.getTrackName = MagicMock(return_value = 'Mugello')
        self.thing.logTrack(1001)

        self.thing.database.getTrackName.assert_called_once()

    def testLogCar(self):
        self.thing.database.getCarName = MagicMock(return_value = 'Porsche 911')
        self.thing.logCar(911)

        self.thing.database.getCarName.assert_called_once()

    def testHandleAmbiguities(self):
        self.thing.ambiguousResultHandler = MagicMock()
        self.thing.car = [100, 200]
        self.thing.logCar = MagicMock()
        self.thing.ambiguousResultHandler.handleAmbiguousCars = MagicMock(return_value=100)
        self.thing.ambiguousResultHandler.handleAmbiguousTracks = MagicMock(return_value=1000)

        result = self.thing.handleAmbiguities(123456789)

        self.thing.ambiguousResultHandler.handleAmbiguousCars.assert_called_once()
        self.thing.ambiguousResultHandler.handleAmbiguousTracks.assert_called_once()
        self.thing.logCar.assert_called_once_with(100)

        self.assertEqual(result, (1000, 100))

if __name__ == "__main__":
    unittest.main()
