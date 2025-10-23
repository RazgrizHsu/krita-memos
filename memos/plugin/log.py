import time
import threading

class _Logger:

    debug = True
    msgBuffer = []
    lastTime = 0
    bufferMs = 100
    timer = None
    lastMsgTime = {}
    dedupeSeconds = 5

    @classmethod
    def log(cls, msg, silent=False):
        if not cls.debug or silent:
            return

        nowMs = int(time.time() * 1000)

        if msg in cls.lastMsgTime:
            lastMs = cls.lastMsgTime[msg]
            if (nowMs - lastMs) < (cls.dedupeSeconds * 1000):
                return

        cls.lastMsgTime[msg] = nowMs
        cls.msgBuffer.append(msg)
        cls.lastTime = nowMs

        if cls.timer is None:
            cls._startTimer()

    @classmethod
    def _startTimer(cls):
        cls.timer = threading.Timer(cls.bufferMs / 1000.0, cls._onTimer)
        cls.timer.daemon = True
        cls.timer.start()

    @classmethod
    def _onTimer(cls):
        cls.timer = None
        if cls.msgBuffer:
            cls._flushBuffer()

    @classmethod
    def _flushBuffer(cls):
        if not cls.msgBuffer:
            return

        if len(cls.msgBuffer) == 1:
            print(f"[Memos] {cls.msgBuffer[0]}")
            cls.msgBuffer = []
            return

        uniqueMsgs = {}
        for msg in cls.msgBuffer:
            uniqueMsgs[msg] = uniqueMsgs.get(msg, 0) + 1

        if len(uniqueMsgs) == 1:
            msg = list(uniqueMsgs.keys())[0]
            count = uniqueMsgs[msg]
            print(f"[Memos] {msg}")
            if count > 1:
                print(f"... (repeated {count - 1} times)")
            cls.msgBuffer = []
            return

        patternLen, patternStart = cls._detectPattern()

        if patternLen > 0:
            for i in range(patternStart):
                print(f"[Memos] {cls.msgBuffer[i]}")

            pattern = cls.msgBuffer[patternStart:patternStart + patternLen]
            repeatCount = (len(cls.msgBuffer) - patternStart) // patternLen

            for msg in pattern:
                print(f"[Memos] {msg}")

            if repeatCount > 1:
                print(f"... (repeated {repeatCount - 1} times)")

            remaining = (len(cls.msgBuffer) - patternStart) % patternLen
            if remaining > 0:
                for i in range(len(cls.msgBuffer) - remaining, len(cls.msgBuffer)):
                    print(f"[Memos] {cls.msgBuffer[i]}")

            cls.msgBuffer = []
            return

        else:
            for msg in cls.msgBuffer:
                print(f"[Memos] {msg}")

        cls.msgBuffer = []

    @classmethod
    def _detectPattern(cls):
        bufLen = len(cls.msgBuffer)

        if bufLen < 4:
            return 0, 0

        for startPos in range(bufLen - 3):
            maxPatternLen = min((bufLen - startPos) // 2, 10)

            for patternLen in range(2, maxPatternLen + 1):
                pattern = cls.msgBuffer[startPos:startPos + patternLen]

                nextPattern = cls.msgBuffer[startPos + patternLen:startPos + patternLen * 2]
                if len(nextPattern) < patternLen:
                    continue

                if pattern == nextPattern:
                    if len(set(pattern)) == 1:
                        continue

                    return patternLen, startPos

        return 0, 0

    @classmethod
    def warn(cls, msg):
        cls._flushBuffer()
        if cls.debug:
            print(f"[Memos WARN] {msg}")
        cls.lastTime = int(time.time() * 1000)

    @classmethod
    def error(cls, msg):
        cls._flushBuffer()
        print(f"[Memos ERROR] {msg}")
        cls.lastTime = int(time.time() * 1000)

    @classmethod
    def setDebug(cls, enabled):
        cls.debug = enabled


lg = _Logger()
