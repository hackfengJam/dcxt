# -*- coding: utf-8 -*-

from functools import wraps, cmp_to_key

import re
import json

patten_email = "^(?:[a-z\d]+[_\-\+\.]?)*[a-z\d]+@(?:([a-z\d]+\-?)*[a-z\d]+\.)+([a-z]{2,})+$"
re_email = re.compile(patten_email, re.I)

DIRECTIVES = {}

def register_directive(key):
    def decorator(f):
        DIRECTIVES[key] = f

        @wraps(f)
        def wrapped_directive(*args, **kwargs):
            return f(*args, **kwargs)

    return decorator

@register_directive('$type')
def _type(v, t):
    t = t.lower()
    if t in ('str', 'string', 'commaarray', 'enum'):
        return isinstance(v, (str, unicode))

    elif t in ('num', 'number', 'float'):
        return isinstance(v, (int, float))

    elif t in ('int', 'integer'):
        return isinstance(v, int)

    elif t in ('bool', 'boolean'):
        return isinstance(v, bool)

    elif t in ('arr', 'array'):
        return isinstance(v, (tuple, list))

    elif t in ('json', 'obj', 'object'):
        return isinstance(v, dict)

    elif t in ('jsonstring',):
        try:
            json.loads(v)
            return True
        except:
            return False

    else:
        return True

@register_directive('$assertTrue')
def _assert_true(v, func):
    return func(v) == True

@register_directive('$assertFalse')
def _assert_false(v, func):
    return func(v) == False

@register_directive('$notEmptyString')
def _not_empty_string(v, flg):
    if not isinstance(v, (str, unicode)):
        return False

    return flg == (len(v) > 0)

@register_directive('$isInteger')
def _is_integer(v, flg):
    return flg == isinstance(v, int)

@register_directive('$isPositiveZeroInteger')
def _is_positive_zero_integer(v, flg):
    return flg == (isinstance(v, int) and v >= 0)

@register_directive('$isPositiveIntegerOrZero')
def _is_positive_integer_or_zero(v, flg):
    return _is_positive_zero_integer(v, flg)

@register_directive('$isPositiveInteger')
def _is_positive_integer(v, flg):
    return flg == (isinstance(v, int) and v > 0)

@register_directive('$isNegativeZeroInteger')
def _is_negative_zero_integer(v, flg):
    return flg == (isinstance(v, int) and v <= 0)

@register_directive('$isNegativeIntegerOrZero')
def _is_negative_integer_or_zero(v, flg):
    return _is_negative_zero_integer(v, flg)

@register_directive('$isNegativeInteger')
def _is_negative_integer(v, flg):
    return flg == (isinstance(v, int) and v < 0)

@register_directive('$minValue')
def _min_value(v, min_value):
    return v >= min_value

@register_directive('$maxValue')
def _max_value(v, max_value):
    return v <= max_value

@register_directive('$isValue')
def _is_value(v, value):
    return v == value

@register_directive('$in')
def _in(v, in_options):
    return v in in_options

@register_directive('$commaArrayIn')
def _comma_array_in(v, in_options):
    v = v.split(',')

    in_option_map = dict([(x, True) for x in in_options])

    for elem in v:
        if not in_option_map.get(elem):
            return False

    return True

@register_directive('$notIn')
def _not_in(v, in_options):
    return v not in in_options

@register_directive('$minLength')
def _min_length(v, min_length):
    if not isinstance(v, (str, unicode, tuple, list)):
        return False

    return len(v) >= min_length

@register_directive('$maxLength')
def _max_length(v, max_length):
    if not isinstance(v, (str, unicode, tuple, list)):
        return False

    return len(v) <= max_length

@register_directive('$isLength')
def _max_length(v, max_length):
    if not isinstance(v, (str, unicode, tuple, list)):
        return False

    return len(v) == max_length

@register_directive('$matchRegExp')
def _match_regexp(v, regexp):
    return (re.match(regexp, str(v)) != None)

@register_directive('$notMatchRegExp')
def _not_match_regexp(v, regexp):
    return (re.match(regexp, str(v)) == None)

@register_directive('$isEmail')
def _is_email(v, flg):
    return flg == (re_email.match(v) != None)

# Functional methods
def create_error_message(e, template):
    error_message = template.get(e.type)
    if error_message:
        error_message = error_message.replace('{{fieldName}}', e.field_name)
    else:
        error_message = str(e)

    if (e.type == 'invalid'):
        error_message = error_message.replace('{{fieldValue}}', json.dumps(e.field_value or ''))
        error_message = error_message.replace('{{checkerName}}', (e.checker_name or '')[1:])
        error_message = error_message.replace('{{checkerOption}}', json.dumps(e.checker_option or ''))

    return error_message

class Nothing(object):
    pass

nothing = Nothing()

class ObjectCheckerException(Exception):
    def __init__(self, type_=None, field_name=None, field_value=None, checker_name=None, checker_option=None):
        self.type           = type_
        self.field_name     = field_name
        self.field_value    = field_value
        self.checker_name   = checker_name
        self.checker_option = checker_option

class ObjectChecker(object):
    def __init__(self, default_required=None, message_template=None, custom_directives=None):
        if default_required is None:
            self.default_required = True
        else:
            self.default_required = default_required

        if message_template is None:
            self.message_template = {
                'invalid'   : "Field `{{fieldName}}` value `{{fieldValue}}` is not valid. ({{checkerName}} = {{checkerOption}})",
                'missing'   : "Field `{{fieldName}}` is missing.",
                'unexpected': "Found unexpected field `{{fieldName}}`"
            }
        else:
            self.message_template = message_template

        if custom_directives is None:
            self.custom_directives = {}
        else:
            self.custom_directives = custom_directives

    def verify(self, obj, options, obj_name=None):
        if obj_name is None:
            obj_name = 'obj'

        options = options or {}

        if self.default_required is True \
                and (options.get('$isOptional') or options.get('$optional')) is True \
                and obj is nothing:
            return

        if self.default_required is False \
                and (options.get('$isRequired') or options.get('$required')) is not True \
                and obj is nothing:
            return

        if options.get('$allowNull') is True and obj is None:
            return

        if obj is nothing:
            raise ObjectCheckerException(
                type_='missing',
                field_name=(obj_name or 'obj'))

        obj_type = options.get('$type', '').lower()
        if options.get('$skip') is True or obj_type in ('any', '*'):
            return

        if isinstance(obj, dict) and obj_type not in ('json', 'obj', 'object'):
            for obj_key in obj.keys():
                if obj_key not in options:
                    raise ObjectCheckerException(
                        type_='unexpected',
                        field_name=obj_key)


        def type_check_first_cmp(x, y):
            if x[0] == '$type':
                return -1
            elif y[0] == '$type':
                return 1

            return 0

        for option_key, option in sorted(options.items(), key=cmp_to_key(type_check_first_cmp)):
            has_option = False
            check_func = None

            if option_key in DIRECTIVES:
                has_option = True
                check_func = DIRECTIVES.get(option_key)

            if option_key in self.custom_directives:
                has_option = True
                check_func = self.custom_directives.get(option_key)

            if has_option:
                if not check_func:
                    continue

                check_result = check_func(obj, option)
                if check_result is False:
                    raise ObjectCheckerException(
                        type_='invalid',
                        field_name=obj_name,
                        field_value=obj,
                        checker_name=option_key,
                        checker_option=option)

            else:
                if option_key in ('$isOptional', '$optional', '$isRequired', '$required', '$allowNull'):
                    # no op
                    pass

                elif option_key == '$':
                    if not isinstance(obj, (tuple, list)):
                        raise ObjectCheckerException(
                            type_='invalid',
                            field_name=obj_name,
                            field_value=obj,
                            checker_name=option_key,
                            checker_option=option)

                    for i in range(len(obj)):
                        element = obj[i]
                        self.verify(element, option, '{}[{}]'.format(obj_name, i))

                else:
                    self.verify(obj.get(option_key, nothing), option, option_key)

    def is_valid(self, obj, options):
        try:
            self.verify(obj, options, 'obj')

        except ObjectCheckerException:
            return False

        return True

    def check(self, obj, options):
        ret = {
            'isValid': True,
            'message': None,
            'detail' : None,
        }

        try:
            self.verify(obj, options, 'obj')

        except ObjectCheckerException as error:
            ret['isValid'] = False
            ret['message'] = create_error_message(error, self.message_template)
            ret['detail'] = {
                'type'         : error.type,
                'fieldName'    : error.field_name,
                'fieldValue'   : error.field_value,
                'checkerName'  : error.checker_name,
                'checkerOption': error.checker_option,
            }

        return ret
