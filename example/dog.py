# class Owner():
#     def __init__(self, name="hooman", age=21):
#         self.name=name
#         self.age=age
        
class Dog():
    def __init__(self, name="unnamed", breed="undefined"):
        self.name = name
        self.tricks = []
        self.breed = breed
        self.happiness = 100
     #   self.owner = Owner()
    
    def add_trick(self, new_trick: str):
        self.tricks.append(new_trick)
        return self.tricks
    
    def pet(self):
        self.happiness += 10
        name =  str(self.name)
        return name+" is happier now!"
    
    
    
typeDict = {
        "<class 'str'>": "%String", 
        "<class 'int'>": "%Integer",
        "<class 'float'>": "%Decimal"
    }   
    
    
    
def get_properties(myClass):
    properties = {}
    typeList = []
    for attribute in dir(myClass):
        property = getattr(myClass, attribute)
        if not attribute.startswith("__") and not callable(property):
            if str(type(property)) in typeDict.keys():
                typeList.append(typeDict[str(type(property))])
            else:
                typeList.append("%SYS.Python")
            
            if type(property) is str:
                property = '"'+property+'"'
            elif type(property) is not int and type(property) is not float:
                property = '""'
                
            properties[attribute] = property
                   
    return properties, typeList


def get_functions(myClass,builtin=False):
    functionsList = [attribute
                     for attribute in dir(myClass)
                     if callable(getattr(myClass, attribute))]
    if not builtin:
        functionsList = [function
                         for function in functionsList
                         if not function.startswith("__")]
        
    return functionsList


def get_implementation(function):
    import inspect as i
    import string
    implementation = i.getsource(function)
    implementation = implementation.split("):")[1]
    inspection = i.getfullargspec(function)
    defaults = inspection.defaults
    annotation = inspection.annotations
    arguments = inspection[0]
    
    if arguments[0] == "self":
        isClassMethod = 0
        arguments.remove("self")
    else:
        isClassMethod = 1
    
    formal_spec = ""
    for argument in arguments:
        translation = argument.translate(str.maketrans('','',string.punctuation))
        if argument in annotation.keys():
            formal_spec += translation+":"+typeDict[str(annotation[argument])]+","
        else:
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
        propertyDict, typeList = get_properties(myClass)
        swizzled = {}
        for i in range(len(propertyDict)):
            newProperty = irispy.classMethodObject("%Dictionary.PropertyDefinition", "%New", className+":"+list(propertyDict)[i])
            newProperty.set("Type", typeList[i])
            if typeList[i] == "%SYS.Python":
                swizzled[list(propertyDict)[i]] = typeList[i]
            newProperty.set("InitialExpression", list(propertyDict.values())[i])
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
            newClass.get("Methods").invoke("Insert", newMethod)
            
        # add %OnNew method when necessary
        if len(swizzled)!=0:
            onNewMethod = irispy.classMethodObject("%Dictionary.MethodDefinition", "%New", className+":"+"%OnNew")
            onNewMethod.set("ClassMethod", 0)
            onNewMethod.set("ReturnType", "%Status")
            onNewMethod.get("Implementation").invoke("WriteLine", "    Set SC = $$$OK")
            onNewMethod.get("Implementation").invoke("Write", "\n    Try\n    {\n")
            for property in swizzled:
                if swizzled[property] in dir(__builtins__):
                    onNewMethod.get("Implementation").invoke("WriteLine", "        Set .."+property+" = ##class(%SYS.Python).Builtins()."+swizzled[property]+"()")
                else:
                    onNewMethod.get("Implementation").invoke("WriteLine", "        Set .."+property+" = ##class(%SYS.Python).%New()")
            
            onNewMethod.get("Implementation").invoke("Write", "\n    }\n    Catch Ex\n    {\n        Set SC = Ex.AsStatus()\n    }\n")
            onNewMethod.get("Implementation").invoke("WriteLine", "    Quit SC")
                    
            newClass.get("Methods").invoke("Insert", onNewMethod)
            
        # saves class
        sc = newClass.invoke("%Save")
        if irispy.classMethodObject("%SYSTEM.Status", "IsError", sc):        
            raise Exception(irispy.classMethodObject('%SYSTEM.Status', 'GetErrorText', sc))
        
    except Exception as error:
        worked = False
        print(error)
        
    return worked

# the definition should set default values for the __init__ method.
# if schema is not specified, the default will be User
# doesn't re-create if there's already a class with that name

# TODO: include annotations for arguments
# TODO: adjust trailing spaces for implementation
if __name__=="__main__":
    print(send_iris(Dog(), "python"))