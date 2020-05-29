from api import API


instance = API("isa", "email", "password", isHeadless=True, updateIntervalRequested=0)
#instance.buy(desiredInstrument="TSLA", numberOfShares=0.001)
instance.getPrice("")