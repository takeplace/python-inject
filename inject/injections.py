from inject import errors
from inject.injection import Injection


'''
@var super_param: empty object which is used to specify that a param 
    is injected in a super class.
'''
super_param = object()


class attr(object):
    
    injection_class = Injection
    
    def __init__(self, attr, type, annotation=None, scope=None, bindto=None):
        self.attr = attr
        self.injection = self.injection_class(type, annotation, scope, bindto) 
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        obj = self.injection.get_instance()
        
        setattr(instance, self.attr, obj)
        return obj


class param(object):
    
    injection_class = Injection
    
    def __new__(cls, name, type, annotation=None, scope=None, bindto=None):
        injection = cls.injection_class(type, annotation, scope, bindto)
        
        def decorator(func):
            if getattr(func, 'injection_wrapper', False):
                # It is already a wrapper.
                wrapper = func
            else:
                wrapper = cls.create_wrapper(func)
            cls.add_injection(wrapper, name, injection)
            return wrapper
        
        return decorator
    
    @classmethod
    def create_wrapper(cls, func):
        injections = {}
        
        def injection_wrapper(*args, **kwargs):
            '''Injection wrapper gets non-existent keyword arguments
            from injections, combines them with kwargs, and passes to
            the wrapped function.
            '''
            for name in injections:
                if name in kwargs and kwargs[name] is not super_param:
                    continue
                
                injection = injections[name]
                kwargs[name] = injection.get_instance()
            
            return func(*args, **kwargs)
        
        # Store the attributes in a wrapper for other functions.
        # Inside the wrapper access them from the closure.
        # It is about 10% faster.
        injection_wrapper.func = func
        injection_wrapper.injections = injections
        injection_wrapper.injection_wrapper = True
        
        return injection_wrapper
    
    @classmethod
    def add_injection(cls, wrapper, name, injection):
        func = wrapper.func
        func_code = func.func_code
        flags = func_code.co_flags
        
        if not flags & 0x04 and not flags & 0x08:
            # 0x04 func uses args
            # 0x08 func uses kwargs
            varnames = func_code.co_varnames
            if name not in varnames:
                raise errors.NoParamError(
                    '%s does not accept an injected param "%s".' %
                    (func, name))
        
        wrapper.injections[name] = injection