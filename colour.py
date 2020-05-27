def error(message=""):
    print("\033[1;31;40m" + str(message))
    
def consoleTag(message=""):
    print("\033[1;36;40m" + str(message))

def returnConsoleTag(message=""):
    return "\033[1;36;40m" + str(message)

def normalTag(message=""):
    print("\033[0;37;40m" + str(message))
    
def returnNormalTag(message=""):
    return "\033[0;37;40m" + str(message)

def output(message=""):\
    print("\033[1;37;40m" + str(message))

def blankSpace(lines=1):
    for i in range(0, lines):
        output()

class PrintManager:
    def __init__(self):
        1+1