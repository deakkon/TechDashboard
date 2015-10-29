'''
Created on 8 Sep 2015

@author: jurica

Timer functios to perodically check for updates of the feed
'''

#===============================================================================
# from threading import Timer
#
#
# class RepeatedTimer(object):
#     def __init__(self, interval, function, *args, **kwargs):
#         self._timer     = None
#         self.interval   = interval
#         self.function   = function
#         self.args       = args
#         self.kwargs     = kwargs
#         self.is_running = False
#         self.start()
# 
#     def get_timer(self):
#         return self.__timer
# 
# 
#     def get_interval(self):
#         return self.__interval
# 
# 
#     def get_function(self):
#         return self.__function
# 
# 
#     def get_args(self):
#         return self.__args
# 
# 
#     def get_kwargs(self):
#         return self.__kwargs
# 
# 
#     def get_is_running(self):
#         return self.__is_running
# 
# 
#     def set_timer(self, value):
#         self.__timer = value
# 
# 
#     def set_interval(self, value):
#         self.__interval = value
# 
# 
#     def set_function(self, value):
#         self.__function = value
# 
# 
#     def set_args(self, value):
#         self.__args = value
# 
# 
#     def set_kwargs(self, value):
#         self.__kwargs = value
# 
# 
#     def set_is_running(self, value):
#         self.__is_running = value
# 
# 
#     def del_timer(self):
#         del self.__timer
# 
# 
#     def del_interval(self):
#         del self.__interval
# 
# 
#     def del_function(self):
#         del self.__function
# 
# 
#     def del_args(self):
#         del self.__args
# 
# 
#     def del_kwargs(self):
#         del self.__kwargs
# 
# 
#     def del_is_running(self):
#         del self.__is_running
# 
# 
#     def _run(self):
#         self.is_running = False
#         self.start()
#         self.function(*self.args, **self.kwargs)
# 
#     def start(self):
#         if not self.is_running:
#             self._timer = Timer(self.interval, self._run)
#             self._timer.start()
#             self.is_running = True
# 
#     def stop(self):
#         self._timer.cancel()
#         self.is_running = False
#         
#     timer = property(get_timer, set_timer, del_timer, "timer's docstring")
#     interval = property(get_interval, set_interval, del_interval, "interval's docstring")
#     function = property(get_function, set_function, del_function, "function's docstring")
#     args = property(get_args, set_args, del_args, "args's docstring")
#     kwargs = property(get_kwargs, set_kwargs, del_kwargs, "kwargs's docstring")
#     is_running = property(get_is_running, set_is_running, del_is_running, "is_running's docstring")
#         
#===============================================================================

from apscheduler.schedulers.background import BackgroundScheduler

class APScheduleRepeater():
    pass
    
    