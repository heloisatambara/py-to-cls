class Dog():
    def __init__(self, name, breed):
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