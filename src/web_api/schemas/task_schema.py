from marshmallow import Schema, fields, validate

class TaskSchema(Schema) :
    task_name = fields.String()
    subtask = fields.String(required=False)
    guid = fields.String(required=False, validate=validate.Length(equal=26))
    
class UlidSchema(Schema):
    # ULID validation
    guid = fields.String(required=True, validate=validate.Length(equal=26))