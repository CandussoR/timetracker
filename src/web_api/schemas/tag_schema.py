from marshmallow import Schema, fields, validate


class TagSchema(Schema):
    tag = fields.String()
    guid = fields.String(required=False, validate=validate.Length(equal=26))