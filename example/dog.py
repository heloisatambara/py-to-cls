class Dog():
    def __init__(self, name="unnamed", breed="undefined"):
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


def get_functions(myClass,builtin=False):
    functionsList = [attribute
                     for attribute in dir(myClass)
                     if callable(getattr(myClass, attribute))]
    if not builtin:
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
    import string
    implementation = i.getsource(function)
    implementation = implementation.split(":")[1]
    inspection = i.getfullargspec(function)
    defaults = inspection.defaults
    arguments = inspection[0]
    
    if arguments[0] == "self":
        isClassMethod = 0
        arguments.remove("self")
    else:
        isClassMethod = 1
    
    formal_spec = ""
    for argument in arguments:
        translation = argument.translate(str.maketrans('','',string.punctuation))
        formal_spec += translation+":%String,"
        implementation = implementation.replace(argument, translation)
    
    if defaults is not None:
        for i in range(len(defaults)):
            implementation = "        if "+arguments[i]+" is None: "+arguments[i]+"='"+defaults[i]+"'\n"+implementation
        
    return implementation, formal_spec[:-1], isClassMethod


def send_iris(myClass, schema = ""):
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
            newMethod.set("Language", "python")
            implementation, formal_spec, isClassMethod =  get_implementation(getattr(myClass, method))
            newMethod.get("Implementation").invoke("Write", implementation)
            newMethod.set("ClassMethod", isClassMethod)
            newMethod.set("FormalSpec", formal_spec)
            print(formal_spec)
            newClass.get("Methods").invoke("Insert", newMethod)
            
        # define the %OnNew with default values for parameters
        init = irispy.classMethodObject("%Dictionary.MethodDefinition", "%New", className+":%OnNew")
        init.set("Language", "python")
        implementation, formal_spec, isClassMethod =  get_implementation(getattr(myClass, "__init__"))
        init.get("Implementation").invoke("Write", implementation+"        return True")
        init.set("ClassMethod", isClassMethod)
        init.set("FormalSpec", formal_spec)
        init.set("ReturnType", "%Status")
        newClass.get("Methods").invoke("Insert", init)
        
        # saves class
        newClass.invoke("%Save")
        
    except Exception as error:
        worked = False
        print(error)
        
    return worked

# the definition should set default values for the __init__ method.
# if schema is not specified, the default will be User
# doesn't re-create if there's already a class with that name
# all arguments must have a default

# TODO: include annotations for arguments
# TODO: set initial values for properties
# TODO: adjust property type (lists)
# TODO: adjust trailing spaces for implementation
# TODO: ver o que fazer com o __init__
if __name__=="__main__":
    print(send_iris(Dog(), "pythonclass"))