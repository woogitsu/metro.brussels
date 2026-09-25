extends SceneTree

# Probe uruchamiany tylko w wirtualnym ekranie przez run_1080p.sh.
# Mierzy rzeczywistą scenę; nie dotyka jej stanu ani nie otwiera okna użytkownika.
const WARMUP_US := 5_000_000
const MEASURE_US := 15_000_000

var started_us := 0
var previous_us := 0
var frame_ms: Array[float] = []
var draw_calls: Array[float] = []
var primitives: Array[float] = []
var static_memory: Array[float] = []
var video_memory: Array[float] = []
var process_ms: Array[float] = []
var mesh_triangles_at_warmup := -1
var step_timing_started := false

func _initialize() -> void:
	call_deferred("_start")

func _start() -> void:
	var scene: Node = load("res://Scenes/FirstRun.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	Input.action_press("driver_power")
	started_us = Time.get_ticks_usec()
	previous_us = started_us
	process_frame.connect(_sample)

func _sample() -> void:
	var now := Time.get_ticks_usec()
	var elapsed := now - started_us
	if elapsed >= WARMUP_US and previous_us > 0:
		if not step_timing_started:
			current_scene.call("BeginStepTiming")
			step_timing_started = true
		if mesh_triangles_at_warmup < 0:
			mesh_triangles_at_warmup = _mesh_triangles(current_scene)
		frame_ms.append(float(now - previous_us) / 1000.0)
		draw_calls.append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
		primitives.append(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
		static_memory.append(Performance.get_monitor(Performance.MEMORY_STATIC))
		video_memory.append(Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED))
		process_ms.append(Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
	previous_us = now
	if elapsed >= WARMUP_US + MEASURE_US:
		var step_values: Array[float] = []
		var step_by_speed: Dictionary = {"stopped": [], "slow": [], "moving": []}
		var speeds: Array = Array(current_scene.call("StepTimingSpeedsKmh"))
		for value in current_scene.call("StepTimingsMicroseconds"):
			step_values.append(value)
			var speed: float = speeds[step_values.size() - 1]
			var category := "stopped" if speed < 1.0 else ("slow" if speed < 10.0 else "moving")
			step_by_speed[category].append(value)
		var by_speed_summary := {}
		for category in step_by_speed:
			var values: Array[float] = []
			values.assign(step_by_speed[category])
			by_speed_summary[category] = {"count": values.size(), "us": _summary(values)}
		var result := {
			"frames": frame_ms.size(),
			"resolution": [get_root().size.x, get_root().size.y],
			"frames_drawn": Engine.get_frames_drawn(),
			"frame_ms": _summary(frame_ms),
			"process_ms": _summary(process_ms),
			"scene_step_us": _summary(step_values),
			"scene_steps": step_values.size(),
			"scene_steps_by_speed": by_speed_summary,
			"resident_mesh_triangles_warmup": mesh_triangles_at_warmup,
			"resident_mesh_triangles_end": _mesh_triangles(current_scene),
			"draw_calls": _summary(draw_calls),
			"render_primitives": _summary(primitives),
			"static_memory_bytes": _summary(static_memory),
			"video_memory_bytes": _summary(video_memory),
			"linux_process_memory_kib": _linux_process_memory(),
		}
		print("[PERF] " + JSON.stringify(result))
		quit()

func _summary(values: Array[float]) -> Dictionary:
	if values.is_empty():
		return {}
	values.sort()
	return {
		"min": values[0],
		"median": values[int(values.size() / 2)],
		"p95": values[int(ceil(values.size() * 0.95)) - 1],
		"max": values[values.size() - 1],
	}

func _mesh_triangles(node: Node) -> int:
	var total := 0
	var mesh_instance := node as MeshInstance3D
	if mesh_instance != null and mesh_instance.mesh != null:
		var mesh := mesh_instance.mesh
		for surface in mesh.get_surface_count():
			var arrays := mesh.surface_get_arrays(surface)
			var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
			total += int((indices.size() if not indices.is_empty() else arrays[Mesh.ARRAY_VERTEX].size()) / 3)
	for child in node.get_children():
		total += _mesh_triangles(child)
	return total

func _linux_process_memory() -> Dictionary:
	var status := FileAccess.open("/proc/self/status", FileAccess.READ)
	if status == null:
		return {}
	var memory := {}
	while not status.eof_reached():
		var line := status.get_line()
		for key in ["VmRSS", "VmHWM"]:
			if line.begins_with(key + ":"):
				memory[key] = line.trim_prefix(key + ":").strip_edges().split(" ", false)[0].to_int()
	return memory
