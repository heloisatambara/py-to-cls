# import sql types
from sqlalchemy.sql.sqltypes import Integer, BigInteger, Unicode, Float, Numeric, DateTime, LargeBinary, Boolean, Date, Time, Interval, ARRAY, JSON
import datetime
import decimal

# import sqlalchemy functions
from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import Table, Column
from sqlalchemy.orm import mapper

# dict from https://stackoverflow.com/questions/4165143/easy-convert-betwen-sqlalchemy-column-types-and-python-data-types
py2sql_dict = {
 int: BigInteger,
 str: Unicode,
 float: Float,
 decimal.Decimal: Numeric,
 datetime.datetime: DateTime,
 bytes: LargeBinary,
 bool: Boolean,
 datetime.date: Date,
 datetime.time: Time,
 datetime.timedelta: Interval,
 list: ARRAY,
 dict: JSON
}

def get_functions(myClass,builtin=False):
    functionsList = [attribute
                     for attribute in dir(myClass)
                     if callable(getattr(myClass, attribute))]
    if not builtin:
        functionsList = [function
                         for function in functionsList
                         if not function.startswith("__")]
        
    return functionsList

# TODO: make this better - check if works
py2cos_dict = { 
        str: "%String", 
        int: "%Integer",
        float: "%Decimal"
    }   

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
            formal_spec += translation+":"+py2cos_dict[str(annotation[argument])]+","
        else:
            formal_spec += translation+":%String,"
            
        implementation = implementation.replace(argument, translation)

    if defaults is not None:
        for i in range(len(defaults)):
            implementation = "        if "+arguments[i]+" is None: "+arguments[i]+"='"+defaults[i]+"'\n"+implementation
        
    return implementation, formal_spec[:-1], isClassMethod


def get_properties(my_class):
    properties = []

    for attribute in dir(my_class):
        property = getattr(my_class, attribute)
        if not attribute.startswith("__") and not callable(property):
            properties.append((attribute, py2sql_dict[type(property)] ,property))
                   
    return properties


def send_iris2(my_class, schema = ""):
    status_code = True
    try:
        # connect to the instance 
        connection_string, user, password = "localhost:1972/SAMPLE", "_system", "sys"
        engine = create_engine("iris://"+user+":"+password+"@"+connection_string)
        import iris
        connection = iris.connect(connection_string, user, password)
        irispy = iris.createIRIS(connection)
        
        # create the table for the class
        class_name = schema+"."+my_class.__class__.__name__
        print(class_name)
        metadata = MetaData()
        table = Table(class_name, metadata, Column('id', Integer,  primary_key=True))
        property_list = get_properties(my_class)
        
        for i in range(len(property_list)):
            table.append_column(property_list[i][0],property_list[i][1], default=property_list[i][2] )
            
        mapper(my_class, table)
        metadata.create_all(engine)
        
        # add methods
        new_class = irispy.classMethodObject("%Dictionary.ClassDefinition", "%Open", class_name)
        method_list = get_functions(my_class)
        for method in method_list:
            newMethod = irispy.classMethodObject("%Dictionary.MethodDefinition", "%New", class_name+":"+method)
            newMethod.set("Language", "python")
            implementation, formal_spec, isClassMethod =  get_implementation(getattr(my_class, method))
            newMethod.get("Implementation").invoke("Write", implementation)
            newMethod.set("ClassMethod", isClassMethod)
            newMethod.set("FormalSpec", formal_spec)
            new_class.get("Methods").invoke("Insert", newMethod)
            
         # saves class
        sc = new_class.invoke("%Save")
        if irispy.classMethodObject("%SYSTEM.Status", "IsError", sc):        
            raise Exception(irispy.classMethodObject('%SYSTEM.Status', 'GetErrorText', sc))
        
            
    
    except Exception as error:
        status_code = False
        print(error)
    
    return status_code