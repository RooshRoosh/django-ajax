from django.utils.translation import ugettext as _
from django.utils.log import getLogger
from django.http import Http404
from django.conf import settings
from decorator import decorator
from ajax.exceptions import AJAXError, PrimaryKeyMissing


logger = getLogger('django.request')


@decorator
def login_required(f, *args, **kwargs):
    if not args[0].user.is_authenticated():
        raise AJAXError(403, _('User must be authenticated.'))

    return f(*args, **kwargs)


@decorator
def require_pk(func, *args, **kwargs):
    if not hasattr(args[0], 'pk') or args[0].pk is None:
        raise PrimaryKeyMissing()

    return func(*args, **kwargs)


@decorator
def json_response(f, *args, **kwargs):
    """Wrap a view in JSON.

    This decorator runs the given function and looks out for ajax.AJAXError's,
    which it encodes into a proper HttpResponse object. If an unknown error
    is thrown it's encoded as a 500.

    All errors are then packaged up with an appropriate Content-Type and a JSON
    body that you can inspect in JavaScript on the client. They look like:

    {
        "message": "Error message here.", 
        "code": 500
    }

    Please keep in mind that raw exception messages could very well be exposed
    to the client if a non-AJAXError is thrown.
    """ 
    try:
        result = f(*args, **kwargs)
        if isinstance(result, AJAXError):
            raise result
    except AJAXError, e:
        result = e.get_response()
    except Http404, e:
        result = AJAXError(404, e.__str__()).get_response()
    except Exception, e:
        import sys
        exc_info = sys.exc_info()
        type, message, trace = exc_info
        if settings.DEBUG:
            import traceback 
            tb = [{'file': l[0], 'line': l[1], 'in': l[2], 'code': l[3]} for 
                l in traceback.extract_tb(trace)]
            result = AJAXError(500, message, traceback=tb).get_response()
        else:
            result = AJAXError(500, "Internal server error.").get_response()

        request = args[0]
        logger.error('Internal Server Error: %s' % request.path,
            exc_info=exc_info,
            extra={
                'status_code': 500,
                'request': request
            }
        )

    result['Content-Type'] = 'application/json'
    return result
