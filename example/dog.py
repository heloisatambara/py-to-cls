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
    
def get_properties(myClass):
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


def get_implementation(function):
    import inspect as i
    implementation = i.getsource(function)
    implementation = implementation.split(":")[1]
    return implementation


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


def send_iris2(myClass, schema = ""):
    worked = True
    try:
        # connect to the instance
        import iris
        connectionString, user, password = "localhost:1972/SAMPLE", "_system", "sys"
        connection = iris.connect(connectionString, user, password)
        irispy = iris.createIRIS(connection)
        
        # create the class
        className = schema+"."+myClass.__class__.__name__
        newClass = irispy.classMethodObject("%Dictionary.ClassDefinition", "%New", className)
        newClass.set("Super", "%Persistent")
        
        # add its properties
        propertyList = get_properties(myClass)
        for property in propertyList:
            newProperty = irispy.classMethodObject("%Dictionary.PropertyDefinition", "%New", className+":"+property)
            newProperty.set("Type", "%String")
            newClass.get("Properties").invoke("Insert", newProperty)
    
        # add its methods
        methodList = get_functions(myClass)
        for method in methodList:
            newMethod = irispy.classMethodObject("%Dictionary.MethodDefinition", "%New", className+":"+method)
            newMethod.set("Language", "Python")
            newMethod.get("Implementation").invoke("Write", get_implementation(getattr(myClass, method)))
            newClass.get("Methods").invoke("Insert", newMethod)
        
        # saves class
        newClass.invoke("%Save")
        
    except Exception as error:
        worked = False
        print(error)
        
    return worked

# the definition should set default values for the __init__ method.
# if schema is not specified, the default will be User

# TODO: method / classmethod if self is an argument
if __name__=="__main__":
    print(send_iris2(Dog(), "pythonclass"))