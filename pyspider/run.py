#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-03-05 00:11:49


import os
import sys
import copy
import time
import shutil
import logging
import logging.config

import click
import pyspider
from pyspider.message_queue import connect_message_queue
from pyspider.database import connect_database
from pyspider.libs import utils


def read_config(ctx, param, value):
    if not value:
        return {}
    import json

    def underline_dict(d):
        if not isinstance(d, dict):
            return d
        return dict((k.replace('-', '_'), underline_dict(v)) for k, v in d.items())

    config = underline_dict(json.load(value))
    ctx.default_map = config
    return config


def connect_db(ctx, param, value):
    if not value:
        return
    return utils.Get(lambda: connect_database(value))


def load_cls(ctx, param, value):
    if isinstance(value, str):
        return utils.load_object(value)
    return value


def connect_rpc(ctx, param, value):
    if not value:
        return
    import xmlrpc.client as xmlrpc_client
    # Python 3.13 compatibility: add timeout and handle connection errors
    try:
        return xmlrpc_client.ServerProxy(value, allow_none=True, use_builtin_types=True,
                                        transport=xmlrpc_client.Transport(use_builtin_types=True))
    except Exception as e:
        import logging
        logging.exception("Failed to connect to RPC server: %s", e)
        raise


@click.group(invoke_without_command=True)
@click.option('-c', '--config', callback=read_config, type=click.File('r'),
              help='a json file with default values for subcommands. {"webui": {"port":5001}}')
@click.option('--logging-config', default=os.path.join(os.path.dirname(__file__), "logging.conf"),
              help="logging config file for built-in python logging module", show_default=True)
@click.option('--debug', envvar='DEBUG', default=False, is_flag=True, help='debug mode')
@click.option('--queue-maxsize', envvar='QUEUE_MAXSIZE', default=100,
              help='maxsize of queue')
@click.option('--taskdb', envvar='TASKDB', callback=connect_db,
              help='database url for taskdb, default: sqlite')
@click.option('--projectdb', envvar='PROJECTDB', callback=connect_db,
              help='database url for projectdb, default: sqlite')
@click.option('--resultdb', envvar='RESULTDB', callback=connect_db,
              help='database url for resultdb, default: sqlite')
@click.option('--message-queue', envvar='AMQP_URL',
              help='connection url to message queue, '
              'default: builtin multiprocessing.Queue')
@click.option('--amqp-url', help='[deprecated] amqp url for rabbitmq. '
              'please use --message-queue instead.')
@click.option('--beanstalk', envvar='BEANSTALK_HOST',
              help='[deprecated] beanstalk config for beanstalk queue. '
              'please use --message-queue instead.')
@click.option('--phantomjs-proxy', envvar='PHANTOMJS_PROXY', help="phantomjs proxy ip:port")
@click.option('--puppeteer-proxy', envvar='PUPPETEER_PROXY', help="puppeteer proxy ip:port")
@click.option('--data-path', default='./data', help='data dir path')
@click.option('--add-sys-path/--not-add-sys-path', default=True, is_flag=True,
              help='add current working directory to python lib search path')
@click.version_option(version="0.3.10", prog_name="pyspider")
@click.pass_context
def cli(ctx, **kwargs):
    """
    A powerful spider system in python.
    """
    if kwargs['add_sys_path']:
        sys.path.append(os.getcwd())

    logging.config.fileConfig(kwargs['logging_config'])

    # get db from env
    for db in ('taskdb', 'projectdb', 'resultdb'):
        if kwargs[db] is not None:
            continue
        if os.environ.get('MYSQL_NAME'):
            kwargs[db] = utils.Get(lambda db=db: connect_database(
                'sqlalchemy+mysql+%s://%s:%s/%s' % (
                    db, os.environ['MYSQL_PORT_3306_TCP_ADDR'],
                    os.environ['MYSQL_PORT_3306_TCP_PORT'], db)))
        elif os.environ.get('MONGODB_NAME'):
            kwargs[db] = utils.Get(lambda db=db: connect_database(
                'mongodb+%s://%s:%s/%s' % (
                    db, os.environ['MONGODB_PORT_27017_TCP_ADDR'],
                    os.environ['MONGODB_PORT_27017_TCP_PORT'], db)))
        elif os.environ.get('COUCHDB_NAME'):
            kwargs[db] = utils.Get(lambda db=db: connect_database(
                'couchdb+%s://%s:%s/%s' % (
                    db,
                    os.environ['COUCHDB_PORT_5984_TCP_ADDR'] or 'couchdb',
                    os.environ['COUCHDB_PORT_5984_TCP_PORT'] or '5984',
                    db)))
        elif ctx.invoked_subcommand == 'bench':
            if kwargs['data_path'] == './data':
                kwargs['data_path'] += '/bench'
                shutil.rmtree(kwargs['data_path'], ignore_errors=True)
                os.mkdir(kwargs['data_path'])
            if db in ('taskdb', 'resultdb'):
                kwargs[db] = utils.Get(lambda db=db: connect_database('sqlite+%s://' % (db)))
            elif db in ('projectdb', ):
                kwargs[db] = utils.Get(lambda db=db: connect_database('local+%s://%s' % (
                    db, os.path.join(os.path.dirname(__file__), 'libs/bench.py'))))
        else:
            if not os.path.exists(kwargs['data_path']):
                os.mkdir(kwargs['data_path'])
            kwargs[db] = utils.Get(lambda db=db: connect_database('sqlite+%s:///%s/%s.db' % (
                db, kwargs['data_path'], db[:-2])))
            kwargs['is_%s_default' % db] = True

    # create folder for counter.dump
    if not os.path.exists(kwargs['data_path']):
        os.mkdir(kwargs['data_path'])

    # message queue, compatible with old version
    if kwargs.get('message_queue'):
        pass
    elif kwargs.get('amqp_url'):
        kwargs['message_queue'] = kwargs['amqp_url']
    elif os.environ.get('RABBITMQ_NAME'):
        kwargs['message_queue'] = ("amqp://guest:guest@%(RABBITMQ_PORT_5672_TCP_ADDR)s"
                                   ":%(RABBITMQ_PORT_5672_TCP_PORT)s/%%2F" % os.environ)

    for name in ('newtask_queue', 'status_queue', 'scheduler2fetcher',
                 'fetcher2processor', 'processor2result'):
        if kwargs.get('message_queue'):
            kwargs[name] = utils.Get(lambda name=name: connect_message_queue(
                name, kwargs.get('message_queue'), kwargs['queue_maxsize']))
        else:
            kwargs[name] = connect_message_queue(name, kwargs.get('message_queue'),
                                                 kwargs['queue_maxsize'])

    # phantomjs-proxy
    if kwargs.get('phantomjs_proxy'):
        pass
    elif os.environ.get('PHANTOMJS_NAME'):
        kwargs['phantomjs_proxy'] = os.environ['PHANTOMJS_PORT_25555_TCP'][len('tcp://'):]

    # puppeteer-proxy
    if kwargs.get('puppeteer_proxy'):
        pass
    elif os.environ.get('PUPPETEER_NAME'):
        kwargs['puppeteer_proxy'] = os.environ['PUPPETEER_PORT_22222_TCP'][len('tcp://'):]

    ctx.obj = utils.ObjectDict(ctx.obj or {})
    ctx.obj['instances'] = []
    ctx.obj.update(kwargs)

    if ctx.invoked_subcommand is None and not ctx.obj.get('testing_mode'):
        ctx.invoke(all)
    return ctx


@cli.command()
@click.option('--xmlrpc', is_flag=True, help="Enable xmlrpc (Default=True)")
@click.option('--no-xmlrpc', is_flag=True, help="Disable xmlrpc")
@click.option('--xmlrpc-host', default='0.0.0.0')
@click.option('--xmlrpc-port', envvar='SCHEDULER_XMLRPC_PORT', default=23333)
@click.option('--inqueue-limit', default=0,
              help='size limit of task queue for each project, '
              'tasks will been ignored when overflow')
@click.option('--delete-time', default=24 * 60 * 60,
              help='delete time before marked as delete')
@click.option('--active-tasks', default=100, help='active log size')
@click.option('--loop-limit', default=1000, help='maximum number of tasks due with in a loop')
@click.option('--fail-pause-num', default=10, help='auto pause the project when last FAIL_PAUSE_NUM task failed, set 0 to disable')
@click.option('--scheduler-cls', default='pyspider.scheduler.ThreadBaseScheduler', callback=load_cls,
              help='scheduler class to be used.')
@click.option('--threads', default=None, help='thread number for ThreadBaseScheduler, default: 4')
@click.pass_context
def scheduler(ctx, xmlrpc, no_xmlrpc, xmlrpc_host, xmlrpc_port,
              inqueue_limit, delete_time, active_tasks, loop_limit, fail_pause_num,
              scheduler_cls, threads, get_object=False):
    """
    Run Scheduler, only one scheduler is allowed.
    """
    g = ctx.obj
    Scheduler = load_cls(None, None, scheduler_cls)

    kwargs = dict(taskdb=g.taskdb, projectdb=g.projectdb, resultdb=g.resultdb,
                  newtask_queue=g.newtask_queue, status_queue=g.status_queue,
                  out_queue=g.scheduler2fetcher, data_path=g.get('data_path', 'data'))
    if threads:
        kwargs['threads'] = int(threads)

    scheduler = Scheduler(**kwargs)
    scheduler.INQUEUE_LIMIT = inqueue_limit
    scheduler.DELETE_TIME = delete_time
    scheduler.ACTIVE_TASKS = active_tasks
    scheduler.LOOP_LIMIT = loop_limit
    scheduler.FAIL_PAUSE_NUM = fail_pause_num

    g.instances.append(scheduler)
    if g.get('testing_mode') or get_object:
        return scheduler

    if not no_xmlrpc:
        utils.run_in_thread(scheduler.xmlrpc_run, port=xmlrpc_port, bind=xmlrpc_host)

    scheduler.run()


@cli.command()
@click.option('--xmlrpc', is_flag=True, help="Enable xmlrpc (Default=True)")
@click.option('--no-xmlrpc', is_flag=True, help="Disable xmlrpc")
@click.option('--xmlrpc-host', default='0.0.0.0')
@click.option('--xmlrpc-port', envvar='FETCHER_XMLRPC_PORT', default=24444)
@click.option('--poolsize', default=100, help="max simultaneous fetches")
@click.option('--proxy', help="proxy host:port")
@click.option('--user-agent', help='user agent')
@click.option('--timeout', help='default fetch timeout')
@click.option('--phantomjs-endpoint', help="endpoint of phantomjs, start via pyspider phantomjs")
@click.option('--puppeteer-endpoint', help="endpoint of puppeteer, start via pyspider puppeteer")
@click.option('--splash-endpoint', help="execute endpoint of splash: http://splash.readthedocs.io/en/stable/api.html#execute")
@click.option('--fetcher-cls', default='pyspider.fetcher.Fetcher', callback=load_cls,
              help='Fetcher class to be used.')
@click.option('--optimize', is_flag=True, help='Enable performance optimization')
@click.option('--memory-check-interval', default=60, help='Memory check interval in seconds')
@click.option('--pool-check-interval', default=30, help='Pool check interval in seconds')
@click.option('--max-memory-percent', default=80, help='Maximum memory usage percentage before optimization')
@click.pass_context
def fetcher(ctx, xmlrpc, no_xmlrpc, xmlrpc_host, xmlrpc_port, poolsize, proxy, user_agent,
            timeout, phantomjs_endpoint, puppeteer_endpoint, splash_endpoint, fetcher_cls,
            optimize, memory_check_interval, pool_check_interval, max_memory_percent,
            async_mode=True, get_object=False, no_input=False):
    """
    Run Fetcher.
    """
    g = ctx.obj

    # Use optimized fetcher if requested
    if optimize:
        from pyspider.fetcher.optimized_async_fetcher import OptimizedAsyncFetcher
        from pyspider.libs.memory_optimizer import memory_optimizer
        from pyspider.fetcher.connection_pool_optimizer import connection_pool_optimizer

        # Configure optimizers
        memory_optimizer.max_memory_percent = max_memory_percent
        memory_optimizer.check_interval = memory_check_interval
        connection_pool_optimizer.check_interval = pool_check_interval

        # Create optimized fetcher
        if no_input:
            inqueue = None
            outqueue = None
        else:
            inqueue = g.scheduler2fetcher
            outqueue = g.fetcher2processor

        # Initialize optimized fetcher
        fetcher = OptimizedAsyncFetcher(
            poolsize=poolsize,
            proxy=proxy,
            timeout=int(timeout) if timeout else 60,
            user_agent=user_agent,
            puppeteer_proxy=puppeteer_endpoint or g.get('puppeteer_proxy'),
            playwright_proxy=None,  # Not used yet
            py_playwright_proxy=None,  # Not used yet
            splash_endpoint=splash_endpoint,
            memory_check_interval=memory_check_interval,
            pool_check_interval=pool_check_interval,
            auto_optimize=True
        )

        # Set up async mode (not used in optimized fetcher but kept for compatibility)
        fetcher.async_mode = async_mode

        # Start optimizers
        memory_optimizer.start()
        connection_pool_optimizer.start()

        logging.info("Using optimized fetcher with performance optimization enabled")
    else:
        # Use standard fetcher
        Fetcher = load_cls(None, None, fetcher_cls)

        if no_input:
            inqueue = None
            outqueue = None
        else:
            inqueue = g.scheduler2fetcher
            outqueue = g.fetcher2processor
        fetcher = Fetcher(inqueue=inqueue, outqueue=outqueue,
                        poolsize=poolsize, proxy=proxy, async_mode=async_mode)
        fetcher.phantomjs_proxy = phantomjs_endpoint or g.phantomjs_proxy
        fetcher.puppeteer_proxy = puppeteer_endpoint or g.puppeteer_proxy
        fetcher.splash_endpoint = splash_endpoint
        if user_agent:
            fetcher.user_agent = user_agent
        if timeout:
            fetcher.default_options = copy.deepcopy(fetcher.default_options)
            fetcher.default_options['timeout'] = timeout

    g.instances.append(fetcher)
    if g.get('testing_mode') or get_object:
        return fetcher

    if not no_xmlrpc:
        utils.run_in_thread(fetcher.xmlrpc_run, port=xmlrpc_port, bind=xmlrpc_host)

    fetcher.run()


@cli.command()
@click.option('--processor-cls', default='pyspider.processor.Processor',
              callback=load_cls, help='Processor class to be used.')
@click.option('--process-time-limit', default=30, help='script process time limit')
@click.pass_context
def processor(ctx, processor_cls, process_time_limit, enable_stdout_capture=True, get_object=False):
    """
    Run Processor.
    """
    g = ctx.obj
    Processor = load_cls(None, None, processor_cls)

    processor = Processor(projectdb=g.projectdb,
                          inqueue=g.fetcher2processor, status_queue=g.status_queue,
                          newtask_queue=g.newtask_queue, result_queue=g.processor2result,
                          enable_stdout_capture=enable_stdout_capture,
                          process_time_limit=process_time_limit)

    g.instances.append(processor)
    if g.get('testing_mode') or get_object:
        return processor

    processor.run()


@cli.command()
@click.option('--result-cls', default='pyspider.result.ResultWorker', callback=load_cls,
              help='ResultWorker class to be used.')
@click.pass_context
def result_worker(ctx, result_cls, get_object=False):
    """
    Run result worker.
    """
    g = ctx.obj
    ResultWorker = load_cls(None, None, result_cls)

    result_worker = ResultWorker(resultdb=g.resultdb, inqueue=g.processor2result)

    g.instances.append(result_worker)
    if g.get('testing_mode') or get_object:
        return result_worker

    result_worker.run()


@cli.command()
@click.option('--host', default='0.0.0.0', envvar='WEBUI_HOST',
              help='webui bind to host')
@click.option('--port', default=5000, envvar='WEBUI_PORT',
              help='webui bind to host')
@click.option('--cdn', default='//cdnjs.cloudflare.com/ajax/libs/',
              help='js/css cdn server')
@click.option('--scheduler-rpc', help='xmlrpc path of scheduler')
@click.option('--fetcher-rpc', help='xmlrpc path of fetcher')
@click.option('--max-rate', type=float, help='max rate for each project')
@click.option('--max-burst', type=float, help='max burst for each project')
@click.option('--username', envvar='WEBUI_USERNAME',
              help='username of lock -ed projects')
@click.option('--password', envvar='WEBUI_PASSWORD',
              help='password of lock -ed projects')
@click.option('--need-auth', is_flag=True, default=False, help='need username and password')
@click.option('--webui-instance', default='pyspider.webui.app.app', callback=load_cls,
              help='webui Flask Application instance to be used.')
@click.option('--process-time-limit', default=30, help='script process time limit in debug')
@click.pass_context
def webui(ctx, host, port, cdn, scheduler_rpc, fetcher_rpc, max_rate, max_burst,
          username, password, need_auth, webui_instance, process_time_limit, get_object=False):
    """
    Run WebUI
    """
    app = load_cls(None, None, webui_instance)

    g = ctx.obj
    app.config['taskdb'] = g.taskdb
    app.config['projectdb'] = g.projectdb
    app.config['resultdb'] = g.resultdb
    app.config['cdn'] = cdn

    if max_rate:
        app.config['max_rate'] = max_rate
    if max_burst:
        app.config['max_burst'] = max_burst
    if username:
        app.config['webui_username'] = username
    if password:
        app.config['webui_password'] = password
    app.config['need_auth'] = need_auth
    app.config['process_time_limit'] = process_time_limit

    # inject queues for webui
    for name in ('newtask_queue', 'status_queue', 'scheduler2fetcher',
                 'fetcher2processor', 'processor2result'):
        app.config['queues'][name] = getattr(g, name, None)

    # fetcher rpc
    if isinstance(fetcher_rpc, str):
        import umsgpack
        try:
            fetcher_rpc = connect_rpc(ctx, None, fetcher_rpc)

            # Python 3.13 compatibility: handle fetch differently
            def safe_remote_fetch(task):
                try:
                    # Convert task to Binary if needed
                    from xmlrpc.client import Binary
                    if isinstance(task, dict):
                        packed_task = umsgpack.packb(task)
                        binary_task = Binary(packed_task)
                        result = fetcher_rpc.fetch(binary_task)
                        return umsgpack.unpackb(result.data)
                    else:
                        result = fetcher_rpc.fetch(task)
                        return umsgpack.unpackb(result.data)
                except Exception as e:
                    import traceback
                    import logging
                    logging.error("Error in remote fetch: %s", e)
                    traceback.print_exc()
                    raise

            app.config['fetch'] = safe_remote_fetch
        except Exception as e:
            import logging
            logging.error("Failed to connect to fetcher RPC: %s", e)
            # Fallback to local fetcher
            fetcher_config = g.config.get('fetcher', {})
            webui_fetcher = ctx.invoke(fetcher, async_mode=False, get_object=True, no_input=True, **fetcher_config)

            def safe_local_fetch(task):
                try:
                    return webui_fetcher.fetch(task)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    raise
            app.config['fetch'] = safe_local_fetch
    else:
        # get fetcher instance for webui
        fetcher_config = g.config.get('fetcher', {})
        webui_fetcher = ctx.invoke(fetcher, async_mode=False, get_object=True, no_input=True, **fetcher_config)

        # In Python 3.13, we need to handle fetch differently to avoid asyncio issues
        def safe_fetch(task):
            try:
                return webui_fetcher.fetch(task)
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise
        app.config['fetch'] = safe_fetch

    # scheduler rpc
    try:
        if isinstance(scheduler_rpc, str):
            scheduler_rpc = connect_rpc(ctx, None, scheduler_rpc)
        if scheduler_rpc is None and os.environ.get('SCHEDULER_PORT_23333_TCP_ADDR'):
            app.config['scheduler_rpc'] = connect_rpc(ctx, None,
                                                    'http://{}:{}/'.format(os.environ.get('SCHEDULER_PORT_23333_TCP_ADDR'),
                                                                           os.environ.get('SCHEDULER_PORT_23333_TCP_PORT') or 23333))
        elif scheduler_rpc is None:
            app.config['scheduler_rpc'] = connect_rpc(ctx, None, 'http://127.0.0.1:23333/')
        else:
            app.config['scheduler_rpc'] = scheduler_rpc
    except Exception as e:
        import logging
        logging.error("Failed to connect to scheduler RPC: %s", e)
        # Create a dummy scheduler_rpc that logs errors and returns appropriate default values
        class DummySchedulerRPC:
            def __getattr__(self, name):
                def dummy_method(*args, **kwargs):
                    logging.error("Scheduler RPC not available. Method %s called with args: %s, kwargs: %s",
                                 name, args, kwargs)

                    # Return appropriate default values for specific methods
                    if name == 'webui_update':
                        return {'counter': {}, 'time': {}, 'pause_status': {}}
                    elif name == 'get_active_tasks':
                        return []
                    elif name == 'counter':
                        return {'active': 0, 'success': 0, 'failed': 0, 'pending': 0}
                    elif name == 'get_queue_stats':
                        return {}
                    else:
                        return None
                return dummy_method
        app.config['scheduler_rpc'] = DummySchedulerRPC()


    app.debug = g.debug
    g.instances.append(app)
    if g.get('testing_mode') or get_object:
        return app

    app.run(host=host, port=port)


# PhantomJS command has been removed as it is deprecated
# Use puppeteer command instead

@cli.command()
@click.option('--port', default=22222, help='puppeteer port')
@click.option('--auto-restart', default=False, help='auto restart puppeteer if crashed')
@click.argument('args', nargs=-1)
@click.pass_context
def puppeteer(ctx, port, auto_restart, args):
    """
    Run puppeteer fetcher if puppeteer is installed.
    """

    import subprocess
    g = ctx.obj
    _quit = []
    puppeteer_fetcher = os.path.join(
        os.path.dirname(pyspider.__file__), 'fetcher/puppeteer_fetcher.js')

    cmd = ['node', puppeteer_fetcher, str(port)]
    try:
        _puppeteer = subprocess.Popen(cmd)
    except OSError:
        logging.warning('puppeteer not found, continue running without it.')
        return None

    def quit(*args, **kwargs):
        _quit.append(1)
        _puppeteer.kill()
        _puppeteer.wait()
        logging.info('puppeteer exited.')

    if not g.get('puppeteer_proxy'):
        g['puppeteer_proxy'] = '127.0.0.1:%s' % port

    puppeteer = utils.ObjectDict(port=port, quit=quit)
    g.instances.append(puppeteer)
    if g.get('testing_mode'):
        return puppeteer

    while True:
        _puppeteer.wait()
        if _quit or not auto_restart:
            break
        _puppeteer = subprocess.Popen(cmd)


@cli.command()
@click.option('--fetcher-num', default=1, help='instance num of fetcher')
@click.option('--processor-num', default=1, help='instance num of processor')
@click.option('--result-worker-num', default=1,
              help='instance num of result worker')
@click.option('--run-in', default='subprocess', type=click.Choice(['subprocess', 'thread']),
              help='run each components in thread or subprocess. '
              'always using thread for windows.')
@click.pass_context
def all(ctx, fetcher_num, processor_num, result_worker_num, run_in):
    """
    Run all the components in subprocess or thread
    """

    ctx.obj['debug'] = False
    g = ctx.obj

    # FIXME: py34 cannot run components with threads
    if run_in == 'subprocess' and os.name != 'nt':
        run_in = utils.run_in_subprocess
    else:
        run_in = utils.run_in_thread

    threads = []

    try:
        # PhantomJS has been removed as it is deprecated

        # puppeteer
        if not g.get('puppeteer_proxy'):
            puppeteer_config = g.config.get('puppeteer', {})
            puppeteer_config.setdefault('auto_restart', True)
            threads.append(run_in(ctx.invoke, puppeteer, **puppeteer_config))
            time.sleep(2)
            if threads[-1].is_alive() and not g.get('puppeteer_proxy'):
                g['puppeteer_proxy'] = '127.0.0.1:%s' % puppeteer_config.get('port', 22222)

        # result worker
        result_worker_config = g.config.get('result_worker', {})
        for i in range(result_worker_num):
            threads.append(run_in(ctx.invoke, result_worker, **result_worker_config))

        # processor
        processor_config = g.config.get('processor', {})
        for i in range(processor_num):
            threads.append(run_in(ctx.invoke, processor, **processor_config))

        # fetcher
        fetcher_config = g.config.get('fetcher', {})
        fetcher_config.setdefault('xmlrpc_host', '127.0.0.1')
        for i in range(fetcher_num):
            threads.append(run_in(ctx.invoke, fetcher, **fetcher_config))

        # scheduler
        scheduler_config = g.config.get('scheduler', {})
        scheduler_config.setdefault('xmlrpc_host', '127.0.0.1')
        threads.append(run_in(ctx.invoke, scheduler, **scheduler_config))

        # running webui in main thread to make it exitable
        webui_config = g.config.get('webui', {})
        webui_config.setdefault('scheduler_rpc', 'http://127.0.0.1:%s/'
                                % g.config.get('scheduler', {}).get('xmlrpc_port', 23333))
        ctx.invoke(webui, **webui_config)
    finally:
        # exit components run in threading
        for each in g.instances:
            each.quit()

        # exit components run in subprocess
        for each in threads:
            if not each.is_alive():
                continue
            if hasattr(each, 'terminate'):
                each.terminate()
            each.join()


@cli.command()
@click.option('--fetcher-num', default=1, help='instance num of fetcher')
@click.option('--processor-num', default=2, help='instance num of processor')
@click.option('--result-worker-num', default=1, help='instance num of result worker')
@click.option('--run-in', default='subprocess', type=click.Choice(['subprocess', 'thread']),
              help='run each components in thread or subprocess. '
              'always using thread for windows.')
@click.option('--total', default=10000, help="total url in test page")
@click.option('--show', default=20, help="show how many urls in a page")
@click.option('--taskdb-bench', default=False, is_flag=True,
              help="only run taskdb bench test")
@click.option('--message-queue-bench', default=False, is_flag=True,
              help="only run message queue bench test")
@click.option('--all-bench', default=False, is_flag=True,
              help="only run all bench test")
@click.pass_context
def bench(ctx, fetcher_num, processor_num, result_worker_num, run_in, total, show,
          taskdb_bench, message_queue_bench, all_bench):
    """
    Run Benchmark test.
    In bench mode, in-memory sqlite database is used instead of on-disk sqlite database.
    """
    from pyspider.libs import bench
    from pyspider.webui import bench_test  # flake8: noqa

    ctx.obj['debug'] = False
    g = ctx.obj
    if result_worker_num == 0:
        g['processor2result'] = None

    if run_in == 'subprocess' and os.name != 'nt':
        run_in = utils.run_in_subprocess
    else:
        run_in = utils.run_in_thread

    all_test = not taskdb_bench and not message_queue_bench and not all_bench

    # test taskdb
    if all_test or taskdb_bench:
        bench.bench_test_taskdb(g.taskdb)
    # test message queue
    if all_test or message_queue_bench:
        bench.bench_test_message_queue(g.scheduler2fetcher)
    # test all
    if not all_test and not all_bench:
        return

    project_name = 'bench'

    def clear_project():
        g.taskdb.drop(project_name)
        g.resultdb.drop(project_name)

    clear_project()

    # disable log
    logging.getLogger().setLevel(logging.ERROR)
    logging.getLogger('scheduler').setLevel(logging.ERROR)
    logging.getLogger('fetcher').setLevel(logging.ERROR)
    logging.getLogger('processor').setLevel(logging.ERROR)
    logging.getLogger('result').setLevel(logging.ERROR)
    logging.getLogger('webui').setLevel(logging.ERROR)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    try:
        threads = []

        # result worker
        result_worker_config = g.config.get('result_worker', {})
        for i in range(result_worker_num):
            threads.append(run_in(ctx.invoke, result_worker,
                                  result_cls='pyspider.libs.bench.BenchResultWorker',
                                  **result_worker_config))

        # processor
        processor_config = g.config.get('processor', {})
        for i in range(processor_num):
            threads.append(run_in(ctx.invoke, processor,
                                  processor_cls='pyspider.libs.bench.BenchProcessor',
                                  **processor_config))

        # fetcher
        fetcher_config = g.config.get('fetcher', {})
        fetcher_config.setdefault('xmlrpc_host', '127.0.0.1')
        for i in range(fetcher_num):
            threads.append(run_in(ctx.invoke, fetcher,
                                  fetcher_cls='pyspider.libs.bench.BenchFetcher',
                                  **fetcher_config))

        # webui
        webui_config = g.config.get('webui', {})
        webui_config.setdefault('scheduler_rpc', 'http://127.0.0.1:%s/'
                                % g.config.get('scheduler', {}).get('xmlrpc_port', 23333))
        threads.append(run_in(ctx.invoke, webui, **webui_config))

        # scheduler
        scheduler_config = g.config.get('scheduler', {})
        scheduler_config.setdefault('xmlrpc_host', '127.0.0.1')
        scheduler_config.setdefault('xmlrpc_port', 23333)
        threads.append(run_in(ctx.invoke, scheduler,
                              scheduler_cls='pyspider.libs.bench.BenchScheduler',
                              **scheduler_config))
        scheduler_rpc = connect_rpc(ctx, None,
                                    'http://%(xmlrpc_host)s:%(xmlrpc_port)s/' % scheduler_config)

        for _ in range(20):
            if utils.check_port_open(23333):
                break
            time.sleep(1)

        scheduler_rpc.newtask({
            "project": project_name,
            "taskid": "on_start",
            "url": "data:,on_start",
            "fetch": {
                "save": {"total": total, "show": show}
            },
            "process": {
                "callback": "on_start",
            },
        })

        # wait bench test finished
        while True:
            time.sleep(1)
            if scheduler_rpc.size() == 0:
                break
    finally:
        # exit components run in threading
        for each in g.instances:
            each.quit()

        # exit components run in subprocess
        for each in threads:
            if hasattr(each, 'terminate'):
                each.terminate()
            each.join(1)

        clear_project()


@cli.command()
@click.option('-i', '--interactive', default=False, is_flag=True,
              help='enable interactive mode, you can choose crawl url.')
@click.option('--puppeteer', 'enable_puppeteer', default=False, is_flag=True,
              help='enable puppeteer, will spawn a subprocess for puppeteer')
@click.argument('scripts', nargs=-1)
@click.pass_context
def one(ctx, interactive, enable_puppeteer, scripts):
    """
    One mode not only means all-in-one, it runs every thing in one process over
    tornado.ioloop, for debug purpose
    """

    ctx.obj['debug'] = False
    g = ctx.obj
    g['testing_mode'] = True

    if scripts:
        from pyspider.database.local.projectdb import ProjectDB
        g['projectdb'] = ProjectDB(scripts)
        if g.get('is_taskdb_default'):
            g['taskdb'] = connect_database('sqlite+taskdb://')
        if g.get('is_resultdb_default'):
            g['resultdb'] = None

    # PhantomJS has been removed as it is deprecated
    phantomjs_obj = None

    if enable_puppeteer:
        puppeteer_config = g.config.get('puppeteer', {})
        puppeteer_obj = ctx.invoke(puppeteer, **puppeteer_config)
        if puppeteer_obj:
            g.setdefault('puppeteer_proxy', '127.0.0.1:%s' % puppeteer.port)
    else:
        puppeteer_obj = None

    result_worker_config = g.config.get('result_worker', {})
    if g.resultdb is None:
        result_worker_config.setdefault('result_cls',
                                        'pyspider.result.OneResultWorker')
    result_worker_obj = ctx.invoke(result_worker, **result_worker_config)

    processor_config = g.config.get('processor', {})
    processor_config.setdefault('enable_stdout_capture', False)
    processor_obj = ctx.invoke(processor, **processor_config)

    fetcher_config = g.config.get('fetcher', {})
    fetcher_config.setdefault('xmlrpc', False)
    fetcher_obj = ctx.invoke(fetcher, **fetcher_config)

    scheduler_config = g.config.get('scheduler', {})
    scheduler_config.setdefault('xmlrpc', False)
    scheduler_config.setdefault('scheduler_cls',
                                'pyspider.scheduler.OneScheduler')
    scheduler_obj = ctx.invoke(scheduler, **scheduler_config)

    scheduler_obj.init_one(ioloop=fetcher_obj.ioloop,
                           fetcher=fetcher_obj,
                           processor=processor_obj,
                           result_worker=result_worker_obj,
                           interactive=interactive)
    if scripts:
        for project in g.projectdb.projects:
            scheduler_obj.trigger_on_start(project)

    try:
        scheduler_obj.run()
    finally:
        scheduler_obj.quit()
        # PhantomJS has been removed as it is deprecated
        if puppeteer_obj:
            puppeteer_obj.quit()


@cli.command()
@click.option('--scheduler-rpc', callback=connect_rpc, help='xmlrpc path of scheduler')
@click.argument('project', nargs=1)
@click.argument('message', nargs=1)
@click.pass_context
def send_message(ctx, scheduler_rpc, project, message):
    """
    Send Message to project from command line
    """
    if isinstance(scheduler_rpc, str):
        scheduler_rpc = connect_rpc(ctx, None, scheduler_rpc)
    if scheduler_rpc is None and os.environ.get('SCHEDULER_PORT_23333_TCP_ADDR'):
        scheduler_rpc = connect_rpc(ctx, None, 'http://%s:%s/' % (os.environ['SCHEDULER_PORT_23333_TCP_ADDR'],
                                                                  os.environ['SCHEDULER_PORT_23333_TCP_PORT'] or 23333))
    if scheduler_rpc is None:
        scheduler_rpc = connect_rpc(ctx, None, 'http://127.0.0.1:23333/')

    return scheduler_rpc.send_task({
        'taskid': utils.md5string('data:,on_message'),
        'project': project,
        'url': 'data:,on_message',
        'fetch': {
            'save': ('__command__', message),
        },
        'process': {
            'callback': '_on_message',
        }
    })


def main():
    cli()

if __name__ == '__main__':
    main()
