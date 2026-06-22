from pydantic import BaseModel

class CategorySchema(BaseModel):
    category_id: int
    code: str
    name: str

    model_config = {
        'from_attributes': True,
        'extra': 'ignore',
    }
