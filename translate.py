import iris

typeDict = {
        "<class 'str'>": "%String", 
        "<class 'int'>": "%Integer",
        "<class 'float'>": "%Decimal",
        "<class 'list'>": "%SYS.Python"
    }   
    
def get_properties(myClass):
    propertyList = []
    typeList = []
    for attribute in dir(myClass):
        property = getattr(myClass, attribute)
        if not attribute.startswith("__") and not callable(property):
            propertyList.append(attribute)
            if str(type(property)) in typeDict.keys():
                typeList.append(typeDict[str(type(property))])
            else:
                typeList.append("%SYS.Python")
            
    return propertyList, typeList


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


def send_iris(connectionString, user, password, myClass, schema = ""):
    worked = True
    try:
        # connect to the instance
        
        connection = iris.connect(connectionString, user, password)
        irispy = iris.createIRIS(connection)
        
        # create the class
        className = schema+"."+myClass.__class__.__name__
        newClass = irispy.classMethodObject("%Dictionary.ClassDefinition", "%New", className)
        newClass.set("Super", "%Persistent")
        
        # add its properties
        propertyList, typeList = get_properties(myClass)
        for i in range(len(propertyList)):
            newProperty = irispy.classMethodObject("%Dictionary.PropertyDefinition", "%New", className+":"+propertyList[i])
            newProperty.set("Type", typeList[i])
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
# you can't have an initial value for a list property

# TODO: include annotations for arguments
# TODO: adjust trailing spaces for implementation
if __name__=="__main__":
    from dog import Dog
    print(send_iris("localhost:1972/SAMPLE", "_system", "sys", Dog(), "python"))