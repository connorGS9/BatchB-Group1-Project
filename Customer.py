from models import user

class Customer:
    def __init__(self, id: int, name: str):
        self.id = id  
        self.name = name

    #ID property, its getters and setter methods
    @property
    def id(self):
        #This gets the customer's privately stored identification number
        return self._id

    @id.setter
    def id(self, value):
        #this sets the customer's ID with a small check to see if it is a valid positive number
        if value < 0:
            raise ValueError("ID cannot be negative!")
        self._id = value

    #Name property, its getters and setter methods
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        # This checks if the name string is a real string value
        if not isinstance(value, str):
            raise TypeError("Name must be a string!")
        
        # This checks if the string value is empty or just blank spaces
        if not value.strip():
            raise ValueError("Name cannot be empty or blank!")
            
        self._name = value
        
