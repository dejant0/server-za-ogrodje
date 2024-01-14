def time_diff(start: float, stop: float, fps):
    t_elapsed = stop - start
    t_frame = 1000 / fps / 1000
    t_diff = t_frame - t_elapsed
    return t_elapsed, t_diff
