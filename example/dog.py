class Dog():
    def __init__(self, name="", breed="undefined"):
        self.name = name
        self.tricks = []
        self.breed = breed
        self.happiness = 100
    
    def add_trick(self, new_trick):
        old_tricks = self.tricks
        self.tricks.append(new_trick)
        return new_trick not in old_tricks
    
    def pet(self):
        self.happiness += 10
        name =  str(self.name)
        return name+" is happier now!"
    
def get_property(myClass):
    propertyList = [attribute
                    for attribute in dir(myClass)
                    if not callable(getattr(myClass, attribute))
                    and not attribute.startswith("__")]
    return propertyList

def get_functions(myClass,builtin=True):
    functionsList = [attribute
                     for attribute in dir(myClass)
                     if callable(getattr(myClass, attribute))]
    if builtin:
        functionsList = [function
                         for function in functionsList
                         if not function.startswith("__")]
    return functionsList
    
def get_dataframe(myClass):
    import pandas as pd
    dataFrame = pd.DataFrame(myClass.__dict__)
    return dataFrame

def send_iris(myClass, schema = ""):
    worked = True
    try:
        from sqlalchemy import create_engine 
        dataFrame = get_dataframe(myClass)
        engine = create_engine("iris://_system:SYS@localhost:1972/SAMPLE")
        dataFrame.to_sql(myClass.__class__.__name__, con=engine, schema=schema, if_exists="replace")
    except Exception as error:
        worked = False
        print(error)
    
    return worked    
    


# the definition should set default values for the __init__ method.

if __name__=="__main__":
    print(send_iris(Dog(), "test"))