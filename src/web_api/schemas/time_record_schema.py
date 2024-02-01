from marshmallow import Schema, fields, post_load, validate

class TimeRecordRequestSchema(Schema):
    '''task_id and tag_id are not required because they are set afterwards.'''
    task_id = fields.String(required=False, validate=validate.Length(equal=26))
    date = fields.Date(required=True)
    time_beginning = fields.Time(required=True)
    time_ending = fields.Time(required=True)
    tag_id = fields.String(required=False, allow_none=True, validate=validate.Length(equal=26))
    log = fields.Str(required=False, allow_none=True)

class TimeRecordBeginningRequestSchema(Schema):
    task_id = fields.String(required=False, validate=validate.Length(equal=26))
    date = fields.Date(required=True)
    time_beginning = fields.Time(required=True) 
    tag_id = fields.String(required=False, allow_none=True, validate=validate.Length(equal=26))

class TimeRecordEndingRequestSchema(Schema):
    guid = fields.String(required=True, validate=validate.Length(equal=26))
    time_ending = fields.Time(required=True)
    log = fields.Str(required=False, allow_none=True)

class TimeRecordSchema(Schema):
    guid = fields.String(attribute='guid')
    task_guid = fields.String(attribute='task_guid')
    date = fields.Date(attribute='date')
    time_beginning = fields.DateTime(attribute='time_beginning')
    time_ending = fields.DateTime(attribute='time_ending')
    time_elapsed = fields.Integer(attribute='time_elapsed')
    tag_guid = fields.String(attribute='tag_guid', required=False, allow_none=True)
    log = fields.String(attribute='log', required=False, allow_none=True)