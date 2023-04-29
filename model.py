class Leaderboard(BaseModel):
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    slug: str
    name: str
    demo: str
    date_added: Optional[datetime]
    date_updated: Optional[datetime]

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data["_id"] is None:
            data.pop("_id")
        return data

class Score(BaseModel):
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    slug: str
    name: str
    score: str
    date_added: Optional[datetime]
    date_updated: Optional[datetime]

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data["_id"] is None:
            data.pop("_id")
        return data