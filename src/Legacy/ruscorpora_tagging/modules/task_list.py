import multiprocessing

TASKS = []

import config


def add_task(in_path, out_path):
    global TASKS
    TASKS.append((in_path, out_path))


def execute_tasks_chunked(in_callback, in_chunk_size=100):
    result = []
    try:
        for task_chunk_index in xrange(0, len(TASKS), in_chunk_size):
            pool = multiprocessing.Pool(processes=config.CONFIG['jobs_number'])
            chunk_begin = task_chunk_size * task_chunk_index
            chunk_end = task_chunk_size * (task_chunk_index + 1)
            chunk_result = pool.map(in_callback, TASKS[chunk_begin:chunk_end])
            pool.close()
            pool.join()
            result += chunk_result
    except:
        pool.terminate()
    return result


def execute_tasks(in_callback, in_pool=None):
    pool = in_pool \
        if in_pool \
        else multiprocessing.Pool(processes=config.CONFIG['jobs_number'])
    try:
        result = pool.map(in_callback, TASKS)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        pool.terminate()
    return result


def execute_tasks_single_thread(in_callback):
    result = [in_callback(task) for task in TASKS]
    return result


def clear_task_list():
    global TASKS
    TASKS = []
