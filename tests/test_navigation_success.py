from sds_eval.task.navigation_env import NavigationEnvironment, NavigationMap
from sds_eval.task.success_checker import reached_goal


def test_navigation_success_and_distance():
    env = NavigationEnvironment(NavigationMap("m", 3, 3, (0, 0), (1, 0)))
    result = env.apply_action("east")
    assert result.valid_action
    assert env.state()["success"]
    assert env.distance_to_goal() == 0
    assert reached_goal(env.state(), env.map.to_dict())


def test_invalid_move_is_rejected():
    env = NavigationEnvironment(NavigationMap("m", 2, 2, (0, 0), (1, 1), obstacles={(1, 0)}))
    result = env.apply_action("east")
    assert not result.valid_action
    assert env.state()["position"] == [0, 0]
    assert env.distance_to_goal() == 2
