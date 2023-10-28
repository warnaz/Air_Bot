from models import CRUD


class Route:
    def __init__(self, id: int, db: CRUD) -> None:
        self.id = id 
        self.actions: list = self.get_action_list(db)
    
    def get_action_list(self, db: CRUD) -> list:
        list_actions = db.get_actions(self.id)
        
        return list_actions
    