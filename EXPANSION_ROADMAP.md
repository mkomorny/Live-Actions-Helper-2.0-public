# Live Actions & Producer Pal Genius — Master Expansion Roadmap & Plan

> **Target Codebase:** `C:\Users\<you>\My Apps\Live Actions Helper`  
> **Codebase References:**  
> - Bridge OSC Layer: `C:\Users\<you>\My Apps\Live Actions Helper\bridge\live-actions-bridge.js`  
> - Pal-Parity LOM Layer: `C:\Users\<you>\My Apps\Live Actions Helper\bridge\live-actions-pal.js`  
> - Python Host Desktop Engine: `C:\Users\<you>\My Apps\Live Actions Helper\app\helper.py`  
> - Producer Pal Genius Client: `C:\Users\<you>\My Apps\Live Actions Helper\app\genius_client.py`  
> - Architectural Constraints: `C:\Users\<you>\My Apps\Live Actions Helper\APP-DETAILS.txt`  
>  
> **Reference Knowledgebases (Drive B):**  
> 1. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\vital_synth_headless_lab` (Vital JSON, DawDreamer, Wavetable/Drift Translation)  
> 2. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton-racks-labeled` (134 Labeled XML Racks, Chains-of-Thought, Macros)  
> 3. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\mixology_db` (90 Multitrack DAW Sessions, 2,411 Gain/Pan Ratios, Parametric EQ Curves, 2,177 Mix Critiques)  
> 4. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_liveapi_tools` (220 LiveAPI Tools, Remote Script TCP Engine, CV Tools, Safe Parameter Randomizer, Hardware MIDI Routing, Browser Loading)  
> 5. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_mcp_extended` (257 LiveAPI Commands, Retrospective Capture MIDI, Arrangement Locators, Drum Rack 128-Pad Muting, Simpler Reflection, 8-Genre Algorithmic Music Engine)  
> 6. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_live_mcp_bschoepke` (Live 12 Local 562MB Sound Similarity DB Search, Arbitrary Python `live_exec`/`live_eval`, Session-to-Arrangement Clip Duplication, Clip Automation Envelopes, Real-time Audio Tap & Spectrograms)
> 7. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_bridge_hidingwill` (359 LiveAPI Tools, ASCII Grid Notation Compiler, Device Preset Snapshotting & LERP Morphing, Algorithmic Euclidean / Polyrhythm Generators, Sidechain Routing, Compound Workflows, Deep M4L Nested Chain Traversal)
> 8. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\abletonosc_ideoforms` (Pure Python Remote Script, UDP 11000/11001, 1-Shot Session JSON Dump, Bulk Multi-Track Queries, Dynamic Hardware MIDI CC Mapping, Track I/O Routing, Real-Time Beat Clock)
> 9. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\pylive_ideoforms` (Object-Oriented Python Client SDK, `live.Set` / `Track` / `Clip`, ASCII Project Tree Dumper, Beat-Synchronized Loop, Generative Clip Walking, Continuous Tempo Modulation)
> 10. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\live_rpyc_lucianoiam` (RPyC Remote Python Call, Direct LOM Memory Proxy `netref`, Port 17744, Cross-Process Listeners, Zero-Protocol Execution)
> 11. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_api_stub_cylab` (Boost.Python XML Schema, 100 Pure-Python Stub Classes, Pre-Execution LOM Validation, Docstring Permissions, Event Listeners, and API Enums)
> 12. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_ai_max9_lom_training` (Remote Scripts v2/v3 Framework, Live 11->12 Runtime Diff with 1,427 Added Members, Cycling '74 Max 9 Live 12.3.5 LOM 200-Page Spec, 74 Native `abl.*` Live DSP Algorithms, and Max 9 V8 / Node for Max `max-api` Integration)
> 13. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\cycling74_max_reference` (Cycling '74 Max 1,805-Object Master Encyclopedia across 16 Packages, MC Multi-Channel Polyphony, Gen~ Low-Level Machine Code DSP, Jitter 3D Audio-Reactivity, and 74 Native `abl.*` Live Algorithms)
> 14. `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\live_12_remote_scripts_reference` (Ableton v3 Modern Framework, 148 Hardware Controller Profiles, Novation Launchkey MK4 Architecture & Sysex Protocol, Push 1/2/3/Move Specs, and Internal `_MxDCore` Bridge Engine)  
>  
> **Status:** Active Master Expansion Roadmap (Audited & Codebase-Aligned)

---

## 1. Master Prompt for Claude (Copy & Paste Ready)

```markdown
Please invoke the live-actions-tool-building-rules skill and implement the Sound Design, Native Rack, Mix Engineering, LiveAPI Suite, AbletonMCP Extended Operations, Sound Similarity Engine, AbletonBridge ASCII Grid & Snapshot Suite, AbletonOSC Remote Script Operations, PyLive Python Client SDK, LiveRPyC Direct Memory Proxy, Ableton Live API Stub Static Validator, Max 9 LOM & Ableton AI Training Engine, Cycling '74 Max 1,805-Object Engine, and Live 12 Remote Scripts Reference (148 Controllers & v3 Framework) into Live Actions Helper and Producer Pal Genius at "C:\Users\<you>\My Apps\Live Actions Helper".

### Context & Reference Datasets
Fourteen complete production-grade datasets have already been compiled and indexed for this on Drive B:
1. Vital Synth Headless Lab: "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\vital_synth_headless_lab"
   - Blueprints: "markdown/04_ableton_live_helper_integration/doc_010_live_actions_host_tool_blueprints.md"
   - Parameter Recipes: "markdown/01_preset_architecture/doc_003_algorithmic_patch_generation_recipes.md"
   - Native Translation Matrix: "markdown/04_ableton_live_helper_integration/doc_009_vital_to_ableton_native_translation_matrix.md"
2. Labeled Ableton Racks: "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton-racks-labeled"
   - 134 extracted XML rack presets in: "xml_presets/"
   - Full BM25 search engine: "search.py"
   - Natural language prompts + Chains-of-Thought: "ableton_racks_labeled_chunks.jsonl"
3. MixologyDB Mix Engineering: "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\mixology_db"
   - Blueprints: "markdown/04_producer_pal_genius_actions/doc_008_producer_pal_auto_balance_blueprint.md", "doc_009_producer_pal_eq_carve_blueprint.md", "doc_010_producer_pal_mix_critique_blueprint.md"
   - Fader & Pan Ratios: "markdown/01_mix_engineering_foundations/doc_002_genre_gain_staging_and_panning_ratios.md"
   - Parametric EQ Curves: "markdown/02_instrument_eq_carving_curves/doc_003_drums_percussion_parametric_eq_profiles.md", "doc_004_bass_guitars_keys_eq_profiles.md", "doc_005_vocal_processing_and_space_curves.md"
   - Mix Critique Rules: "markdown/03_semantic_mix_doctor_and_evaluations/doc_006_mix_critique_taxonomy_and_diagnostic_rules.md", "doc_007_automated_mix_audit_and_remedies.md"
4. Ableton LiveAPI Tools & Remote Script Architecture: "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_liveapi_tools"
   - Source Code & Architecture: "raw_data/liveapi_tools.py", "raw_data/ARCHITECTURE.md", "raw_data/MAX4LIVE_INTEGRATION.md"
   - Blueprints: "markdown/04_producer_pal_genius_integration/doc_009_producer_pal_advanced_live_actions_blueprints.md", "doc_010_dual_engine_hybrid_bridge_architecture.md"
   - CV Tools & Modulation: "markdown/03_max_for_live_and_cv_tools/doc_008_cv_tools_modular_synthesis_recipes.md", "doc_007_max_for_live_dynamic_parameter_discovery.md"
   - Hardware MIDI & Clip Quantization: "markdown/02_tools_catalog_and_categories/doc_006_hardware_midi_cc_and_program_change.md", "doc_003_session_transport_track_and_clip_tools.md"
   - Live 12 Display Values: "markdown/02_tools_catalog_and_categories/doc_004_device_control_and_parameter_introspection.md"
5. AbletonMCP Extended Operations & Algorithmic Music Engine: "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_mcp_extended"
   - Source Code & Architecture: "raw_data/AbletonMCP_Remote_Script___init__.py" (v2.0.0+, 307 KB, 257 commands), "raw_data/docs_TOOLS.md", "raw_data/docs_MANUAL.md"
   - Blueprints: "markdown/04_producer_pal_genius_integration/doc_009_producer_pal_live_actions_blueprints.md", "doc_010_dual_engine_tcp_osc_hybrid_connector.md"
   - Locators & Arrangement: "markdown/02_tools_reference_and_schemas/doc_003_transport_arranger_and_locators.md"
   - Drum Rack & Simpler: "markdown/02_tools_reference_and_schemas/doc_006_devices_drum_racks_and_simpler.md"
   - Algorithmic Music Helpers: "markdown/03_algorithmic_music_helpers/doc_008_algorithmic_drum_and_bassline_generation.md"
6. Sound Similarity & Advanced Live Execution: "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_live_mcp_bschoepke"
   - Source Code & Architecture: "raw_data/similar_sounds.py", "raw_data/server.py", "raw_data/visual_capture.py", "raw_data/agent_audio_tap.js"
   - Blueprints: "markdown/04_producer_pal_genius_integration/doc_009_producer_pal_advanced_actions_blueprints.md", "doc_010_tri_engine_hybrid_architecture.md"
   - Sound Similarity DB & Cosine Engine: "markdown/02_sound_similarity_engine/doc_003_live_12_sound_similarity_db_architecture.md", "doc_004_neural_audio_feature_decoding_and_cosine_search.md"
   - Arbitrary Python Exec: "markdown/01_engine_and_live_exec/doc_001_arbitrary_python_execution_engine.md", "doc_002_live_object_reference_and_batch_pipeline.md"
   - Session-to-Arrangement & Automation: "markdown/03_arrangement_automation_and_telemetry/doc_005_session_to_arrangement_sequencing.md", "doc_006_clip_parameter_and_velocity_automation.md"
   - Audio Tapping & Spectrograms: "markdown/03_arrangement_automation_and_telemetry/doc_008_audio_signal_tapping_and_spectrograms.md"
7. AbletonBridge 359-Tool Suite & ASCII Grid Notation: "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_bridge_hidingwill"
   - Source Code & Architecture: "raw_data/grid_notation.py", "raw_data/creative.py", "raw_data/snapshots.py", "raw_data/devices.py", "raw_data/workflows.py", "raw_data/m4l_bridge.js"
   - Blueprints: "markdown/04_bridge_integration_and_genius_blueprints/doc_009_producer_pal_genius_integration_blueprints.md", "doc_010_compound_workflows_and_production_macros.md"
   - ASCII Grid Compiler: "markdown/02_ascii_grid_and_creative_synthesis/doc_003_ascii_grid_notation_compiler.md"
   - Algorithmic Suite: "markdown/02_ascii_grid_and_creative_synthesis/doc_004_algorithmic_rhythm_and_melody_generators.md"
   - Snapshots & Morphing: "markdown/03_snapshots_sidechain_and_deep_m4l/doc_005_device_preset_snapshotting_and_morphing.md"
   - Sidechain Routing: "markdown/03_snapshots_sidechain_and_deep_m4l/doc_006_sidechain_routing_and_gain_reduction.md"
   - Deep M4L Navigation: "markdown/03_snapshots_sidechain_and_deep_m4l/doc_007_max_for_live_deep_device_and_chain_traversal.md"
8. AbletonOSC Remote Script Suite & Full Session Dump: "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\abletonosc_ideoforms"
   - Source Code & Architecture: "raw_data/abletonosc_song.py", "raw_data/abletonosc_track.py", "raw_data/abletonosc_clip.py", "raw_data/abletonosc_device.py", "raw_data/abletonosc_midimap.py", "raw_data/client_client.py"
   - Blueprints: "markdown/04_producer_pal_genius_integration/doc_009_producer_pal_genius_action_blueprints.md", "doc_010_tri_engine_osc_remote_script_synthesis.md"
   - 1-Shot Structural Dump: "markdown/02_song_track_and_routing_api/doc_005_bulk_session_state_and_structural_export.md"
   - Bulk Multi-Track Query: "markdown/02_song_track_and_routing_api/doc_005_bulk_session_state_and_structural_export.md"
   - Track I/O Bus Routing: "markdown/02_song_track_and_routing_api/doc_004_track_operations_and_bus_io_routing.md"
   - Dynamic Hardware MIDI CC Mapping: "markdown/03_clips_devices_and_midimap/doc_008_hardware_midimap_and_view_navigation.md"
   - 5-Tuple OSC Clip Notes: "markdown/03_clips_devices_and_midimap/doc_006_clip_slot_and_5tuple_midi_operations.md"
   - Real-Time Beat Clock: "markdown/02_song_track_and_routing_api/doc_003_song_control_cue_points_and_beat_clock.md"
9. PyLive Object-Oriented Python Client SDK: "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\pylive_ideoforms"
   - Source Code & Architecture: "raw_data/live_classes_set.py", "raw_data/live_classes_track.py", "raw_data/live_classes_clip.py", "raw_data/live_classes_device.py", "raw_data/live_classes_parameter.py", "raw_data/examples_ex-clip-walk.py", "raw_data/examples_ex-tempo-modulate.py"
   - Blueprints: "markdown/04_producer_pal_genius_integration/doc_009_producer_pal_genius_action_blueprints.md", "doc_010_tri_engine_host_sdk_architecture.md"
   - ASCII Tree Dumper: "markdown/01_architecture_and_object_model/doc_002_live_set_lifecycle_and_dual_scan.md"
   - Semantic Object Lookups: "markdown/02_classes_and_lom_abstractions/doc_003_tracks_groups_and_routing_models.md"
   - Generative Clip Walking: "markdown/03_generative_and_beat_synchronization/doc_007_generative_clip_walking_and_stochastic_playback.md"
   - Beat Synchronization: "markdown/03_generative_and_beat_synchronization/doc_006_beat_synchronized_event_loops.md"
   - Tempo Shaping: "markdown/03_generative_and_beat_synchronization/doc_008_tempo_shaping_and_continuous_modulation.md"
   - Safe Parameter Randomization: "markdown/02_classes_and_lom_abstractions/doc_005_devices_and_safe_parameter_randomizer.md"
10. LiveRPyC Direct Memory Proxy & Zero-Protocol Execution: "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\live_rpyc_lucianoiam"
    - Source Code & Architecture: "raw_data/client.py", "raw_data/LiveRPyC_rpyc_server.py", "raw_data/LiveRPyC_rpyc_control_surface.py", "raw_data/LiveRPyC_lom_observer_helper.py"
    - Blueprints: "markdown/04_producer_pal_genius_integration/doc_009_producer_pal_genius_action_blueprints.md", "doc_010_tri_engine_direct_memory_proxy_synthesis.md"
    - Direct LOM Dereferencing: "markdown/02_lom_proxy_and_cross_process_listeners/doc_003_transparent_lom_dereferencing_and_manipulation.md"
    - Cross-Process Event Listeners: "markdown/02_lom_proxy_and_cross_process_listeners/doc_004_cross_process_event_listeners_and_callbacks.md"
    - Deep Rack Traversal: "markdown/03_deep_introspection_and_note_matrix/doc_005_deep_object_introspection_and_rack_traversal.md"
    - Native C++ Note Specs: "markdown/03_deep_introspection_and_note_matrix/doc_006_direct_cpp_midi_note_specifications.md"
    - Batch Scraper: "markdown/03_deep_introspection_and_note_matrix/doc_007_batch_lom_querying_and_state_scraping.md"
    - Error Handling & Deadlock Prevention: "markdown/04_producer_pal_genius_integration/doc_008_error_handling_deadlock_prevention_and_timeouts.md"
11. Ableton Live API Stub & Pre-Execution Validator: "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_api_stub_cylab"
    - Source Code & Schemas: "raw_data/generate-stub.py", "raw_data/Live.xml", "raw_data/Live___init__.py", "raw_data/README.md"
    - Blueprints: "markdown/04_producer_pal_genius_integration/doc_009_producer_pal_genius_action_blueprints.md", "doc_010_static_verification_and_safety_pipeline.md"
    - Pure-Python Stubs & Offline Import: "markdown/01_architecture_and_type_stubs/doc_001_ableton_api_stub_architecture_and_offline_import.md"
    - Docstrings & Permission Taxonomy: "markdown/01_architecture_and_type_stubs/doc_002_live_xml_schema_and_permission_taxonomy.md"
    - Song & Application Classes: "markdown/02_song_track_and_clip_schemas/doc_003_application_and_song_class_schemas.md"
    - Track & MixerDevice Classes: "markdown/02_song_track_and_clip_schemas/doc_004_track_and_mixer_device_schemas.md"
    - Clip & ClipSlot Classes: "markdown/02_song_track_and_clip_schemas/doc_005_clip_and_clip_slot_schemas.md"
    - Device & Parameter Bounds: "markdown/03_devices_parameters_and_enums/doc_006_device_chain_and_parameter_schemas.md"
    - Quantization & WarpMode Enums: "markdown/03_devices_parameters_and_enums/doc_007_api_enums_quantization_and_warp_modes.md"
    - Browser & File Schemas: "markdown/03_devices_parameters_and_enums/doc_008_browser_and_file_management_schemas.md"
12. Ableton AI & Max 9 LOM Training Engine: "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_ai_max9_lom_training"
    - Source Code & Manuals: "raw_data/Max9 LOM Reference.pdf", "raw_data/Max9 JS API Reference.pdf", "raw_data/Max9 NodeForMax API Reference.pdf", "raw_data/Remote_Scripts_Complete_Guide.md", "raw_data/Runtime_Changes_Live_11_to_12.md", "raw_data/Cycling74_Max_Reference_Guide.md"
    - Blueprints: "markdown/06_producer_pal_genius_integration/doc_015_producer_pal_genius_action_blueprints.md", "doc_016_unified_quad_tier_architecture.md"
    - Remote Scripts Architecture: "markdown/01_remote_scripts_v2_v3_framework/doc_001_remote_scripts_architecture_and_lifecycle.md"
    - Components & Layers: "markdown/01_remote_scripts_v2_v3_framework/doc_002_components_layers_and_modes.md"
    - Status Bar & Pad Layouts: "markdown/01_remote_scripts_v2_v3_framework/doc_004_status_messages_and_pad_layouts.md"
    - Runtime Changes Diff: "markdown/02_runtime_changes_live_11_to_12/doc_005_live_11_to_12_runtime_diff_overview.md"
    - Microtonal Tuning Systems: "markdown/02_runtime_changes_live_11_to_12/doc_006_tuning_systems_and_microtonal_lom.md"
    - Take Lanes & Comping: "markdown/02_runtime_changes_live_11_to_12/doc_007_take_lanes_comping_and_cc_control.md"
    - Max 9 Live 12.3.5 LOM: "markdown/03_max9_lom_and_native_device_classes/doc_008_max9_live_12_lom_specification.md"
    - Flagship Synths (Meld, Roar, Drift): "markdown/03_max9_lom_and_native_device_classes/doc_009_flagship_device_classes_meld_roar_drift.md"
    - Native Ableton DSP (74 abl.* objects): "markdown/04_cycling74_ableton_dsp_and_m4l_objects/doc_011_ableton_dsp_abl_algorithms_catalog.md"
    - Signal-Rate live.remote~ & live.modulate~: "markdown/04_cycling74_ableton_dsp_and_m4l_objects/doc_012_max_for_live_live_objects_and_routing.md"
    - Max 9 V8 & Embedded SQLite: "markdown/05_max9_js_v8_and_node_for_max/doc_013_max9_js_v8_scripting_and_embedded_sqlite.md"
    - Node for Max max-api: "markdown/05_max9_js_v8_and_node_for_max/doc_014_node_for_max_api_and_json_dictionaries.md"
13. Cycling '74 Max 1,805-Object Master Knowledgebase: "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\cycling74_max_reference"
    - Source Code & JSON Catalog: "raw_data/objects.json" (1,805 cataloged objects), "raw_data/guide.md" (73-page reference), "raw_data/cycling74-reference-guide.pdf"
    - Blueprints: "markdown/07_producer_pal_genius_integration/doc_013_producer_pal_genius_action_blueprints.md", "doc_014_complete_1805_object_master_directory.md"
    - Core Max Logic: "markdown/01_core_max_logic_and_timing/doc_001_max_message_architecture_and_data_flow.md"
    - Algorithmic Timing: "markdown/01_core_max_logic_and_timing/doc_002_algorithmic_timing_math_and_clocks.md"
    - MSP Real-Time Audio: "markdown/02_msp_realtime_audio_dsp/doc_003_msp_signal_vectors_and_audio_engine.md"
    - MSP Filters & Envelopes: "markdown/02_msp_realtime_audio_dsp/doc_004_msp_filters_envelopes_and_dynamics.md"
    - MC Multi-Channel Audio: "markdown/03_mc_multichannel_audio_polyphony/doc_005_mc_multichannel_architecture_and_chords.md"
    - MC Voice Dispersion: "markdown/03_mc_multichannel_audio_polyphony/doc_006_mc_voice_dispersion_and_spatial_panning.md"
    - Gen~ Low-Level Machine Code: "markdown/04_gen_lowlevel_dsp_machine_code/doc_007_gen_architecture_and_jit_machine_code.md"
    - Gen Codebox Waveshaping: "markdown/04_gen_lowlevel_dsp_machine_code/doc_008_gen_codebox_waveshaping_and_filters.md"
    - Jitter 3D Geometry: "markdown/05_jitter_3d_video_and_gl_shaders/doc_009_jitter_matrix_processing_and_geometry.md"
    - Jitter GLSL Shaders: "markdown/05_jitter_3d_video_and_gl_shaders/doc_010_jitter_glsl_shaders_and_audio_reactivity.md"
    - Native Ableton DSP (74 abl.*): "markdown/06_ableton_dsp_and_m4l_integration/doc_011_native_ableton_dsp_abl_algorithms.md"
    - M4L UI & Parameter Binding: "markdown/06_ableton_dsp_and_m4l_integration/doc_012_max_for_live_ui_and_parameter_binding.md"
14. Live 12 MIDI Remote Scripts Reference (148 Controllers & v3 Framework): "B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\live_12_remote_scripts_reference"
    - Source Code & Manuals: "raw_data/INDEX.md", "raw_data/frameworks/ableton_v3.md", "raw_data/frameworks/system_frameworks.md", "raw_data/devices/novation_controllers.md", "raw_data/devices/ableton_hardware.md", "raw_data/devices/akai_controllers.md"
    - Blueprints: "markdown/06_producer_pal_genius_integration/doc_014_producer_pal_genius_action_blueprints.md", "doc_015_unified_remote_script_synthesis.md"
    - Ableton v3 Framework Architecture: "markdown/01_ableton_v3_modern_framework/doc_001_ableton_v3_architecture_and_components.md"
    - AutoArm & ActiveParameter Components: "markdown/01_ableton_v3_modern_framework/doc_002_v3_core_components_auto_arm_and_recording.md"
    - Display Line Specifications: "markdown/01_ableton_v3_modern_framework/doc_003_v3_display_lines_and_screen_specs.md"
    - Novation Launchkey MK4 Architecture: "markdown/02_novation_and_launchkey_mk4/doc_005_launchkey_mk4_remote_script_architecture.md"
    - Novation Sysex Protocol & Pad Modes: "markdown/02_novation_and_launchkey_mk4/doc_006_novation_sysex_protocol_and_pad_modes.md"
    - PushBase Architecture (Push 1/2/3): "markdown/03_ableton_hardware_and_push/doc_008_pushbase_architecture_push1_push2_push3.md"
    - Ableton Move Standalone Script: "markdown/03_ableton_hardware_and_push/doc_009_ableton_move_controller_script.md"
    - Akai APC64 & MPC Touch Faders: "markdown/04_third_party_controllers_akai_arturia/doc_010_akai_apc64_and_mpc_remote_scripts.md"
    - Arturia KeyLab & NI Komplete Kontrol: "markdown/04_third_party_controllers_akai_arturia/doc_011_arturia_keylab_and_ni_komplete_kontrol.md"
    - _MxDCore Max for Live Internal Bridge: "markdown/05_mxdcore_and_system_frameworks/doc_012_mxdcore_max_for_live_internal_engine.md"

Review foundational project docs per Step 1 (APP-DETAILS.txt, bridge/live-actions-bridge.js, bridge/live-actions-pal.js, app/helper.py, app/genius_client.py) before writing code.

---

### Strict Codebase & API Conventions (Audited Against Live Actions Helper)

1. **Target Environment**: Ableton Live 12 Standard on Windows. Never use Suite-only APIs or right-click menu extensions.
2. **Device Protection**: Never modify official Max for Live devices (`Producer_Pal.amxd`). All communication flows through the homemade OSC Bridge (`Live Actions Bridge.amxd` on UDP ports 11924 / 11925), the Python Remote Script TCP connector (`AbletonMCP` on port 9877), and local Python SQLite helpers.
3. **Native Device Names**: Must strictly match `PAL_NATIVE_DEVICES` in `bridge/live-actions-pal.js` (lines 1624–1641):
   - Always `"EQ Eight"` (never `"Eq8"`).
   - Always `"EQ Three"`, `"Channel EQ"`, `"Compressor"`, `"Glue Compressor"`, `"Auto Filter"`, `"Saturator"`, `"Chorus-Ensemble"`, `"Drift"`, `"Wavetable"`, `"Simpler"`, `"Drum Rack"`, `"Reverb"`, `"Delay"`.
4. **Live Tool Signatures**: In `app/genius_client.py`, Genius tools must follow the established `live_*` schema:
   - Faders & Pans: `live_update_track(track_index=..., gain_db=..., pan=...)` (where `gain_db` is in decibels, `pan` is -1.0 to 1.0). Do not invent `live_set_track_property`.
   - Reading Set/Track: `live_read_set(include=[...])` and `live_read_track(track_index=..., include=[...])`. Do not use `ppal-read-*`.
   - Device Insertion: `live_create_device(track_index=..., device_name="...", params=[{"name": str, "value": str}])`.
   - Device Updates: `live_update_device(track_index=..., device_index=..., params=[{"name": str, "value": str}])`.
   - Rack Macros: `live_read_macros(track_index=..., device_index=...)`, `live_update_macro(track_index=..., device_index=..., macro_index=..., value=...)`, and `live_map_rack_magnitude(track_index=..., device_index=..., macro_name=...)`.
   - Clip Placement: Session audio clips use `bridge.call_live("create_clip", {"track_index": t, "slot_index": s, "sample_file": path})`; Arrangement clips use `bridge.call_live("create_clip", {"track_index": t, "arrangement_start": "1|1", "sample_file": path})`.
5. **Host Tools (`runtime: "host"`)**:
   - Registered in `HOST_TOOLS` in `app/helper.py`: `HOST_TOOLS[tool_id] = module.run`.
   - Signature: `def run(fields: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]`.
   - Must return `{"ok": bool, "message": str, "path": Optional[str]}`.
   - When `"destination": "Add to Live Set"`, `helper.py`'s worker invokes `_place_generated_file()` which prompts for an empty session slot on the ticked audio track and injects the clip.
6. **Unified Tri-Engine Architecture**:
   - **Engine 1 (OSC Bridge)**: UDP 11924 for instant zero-dependency LOM control (faders, pans, EQ Eight, native device inserts).
   - **Engine 2 (TCP Remote Script)**: Port 9877 for Retrospective MIDI Capture, timeline locators, 128-pad Drum Rack muting, and browser loading.
   - **Engine 3 (Local Desktop Host Engine)**: Queries local 562MB Sound Similarity SQLite database (`Live-files-12300.db`), runs offline Vital WAV baking, and provides the arbitrary Python `live_exec` hook.

---

### What to Build:

#### PART 1: Vital Host Tools (Pure Python Host Runtime)
1. Host Tool: Vital Preset Generator & Morpher (`tools/vital-preset/tool.json` + `app/vital_preset.py`)
   - `"runtime": "host"`.
   - Procedurally generates or mutates `.vital` presets (JSON format) from archetypes (Reese Bass, Neo-Soul Pluck, 80s Synthwave Lead, Ambient Pad, Super Saw).
   - Preset Morphing: Blends two existing `.vital` presets via parameter interpolation (LERP).
   - Sweet-spot randomizer: Keeps resonance, warp, and LFOs within musical limits.
   - Saves to `%USERPROFILE%\Documents\Vital\User\Presets\Live Actions\`.
   - Includes in-app "Audition" pre-listen via local playback.

2. Host Tool: Vital Headless Baker (`tools/vital-render/tool.json` + `app/vital_render.py`)
   - `"runtime": "host"`.
   - Uses DawDreamer or Vita in Python to host Vital headlessly and bounce audio faster-than-realtime.
   - Clip-Aware Bouncing: Reads active MIDI notes directly from the currently ticked track/clip via `bridge.call_live("read_clip", {"track_index": t, "slot_index": s, "include": ["notes"]})`, renders them through Vital at project BPM, and injects the resulting 24-bit WAV directly onto an audio track via `_place_generated_file()`.
   - Saves bakes to `%APPDATA%\Live Actions\Samples\Bakes\`.

3. Host Tool / Genius Converter: Vital-to-Native Device Converter (`tools/vital-to-native/tool.json` + `app/vital_to_native.py`)
   - Reads a `.vital` preset JSON file and translates its parameters into an Ableton Live 12 native **Wavetable** or **Drift** device using the mapping matrix in `vital_synth_headless_lab/markdown/04_ableton_live_helper_integration/doc_009_vital_to_ableton_native_translation_matrix.md`.
   - Calls `live_create_device(track_index=..., device_name="Wavetable", params=[...])` to instantiate and parameterize the native instrument directly on the ticked track with zero VST overhead.

#### PART 2: Producer Pal Genius Native Rack Actions (AI Agent Tool Calling)
Enhance `app/genius_client.py` and the Genius knowledge index to execute 4 high-level autonomous rack actions:

4. Genius Action: Natural Language Rack Builder (`live_create_rack_chain`)
   - When the user asks for a sonic texture in chat (e.g. "warm analog tape channel strip", "3-band parallel reverb", "ambient space delay"):
   - Genius queries `ableton_racks_labeled.db` via `library_db_search`, reads the step-by-step Chain-of-Thought, and emits sequential `live_create_device` calls with exact calibrated parameters, routing, and dry/wet balances using native devices (`"Compressor"`, `"Saturator"`, `"EQ Eight"`, `"Chorus-Ensemble"`).

5. Genius Action: 1-Shot XML-to-.ADG Preset Spooler (`live_spool_adg_preset`)
   - For complex nested racks: fetches the target XML from `ableton-racks-labeled/xml_presets/`, runs Python gzip compression (`gzip.compress(xml_bytes)`), saves the native `.adg` into `A:\User Library\Presets\Audio Effects\Audio Effect Rack\Live Actions Racks\`, and notifies the user for 1-click loading.

6. Genius Action: Intelligent Macro Mapping & Calibration (`live_calibrate_rack_macros`)
   - Uses the `<MacroControls>` specifications in the dataset and `live_map_rack_magnitude` / `live_update_macro` to configure Macros 1–16 on any active Rack, binding parameters to musical min/max sweep ranges.

7. Genius Action: Signal Chain Doctor & Diagnostics (`live_diagnose_signal_chain`)
   - Inspects the active devices on a track via `live_read_track(track_index=..., include=["devices"])`, audits the signal chain against the 134 gold-standard reference chains, and automatically re-orders or optimizes parameters via `live_move_device` and `live_update_device`.

#### PART 3: Producer Pal Genius Mix Engineering Suite (MixologyDB)
Integrate empirical multi-track mixing tools into `app/mix_checker.py` and `app/genius_client.py`:

8. Genius Action: Multi-Track Auto Gain-Staging & Panning (`live_auto_gain_stage`)
   - Queries active tracks in the Live Set (`live_read_set(include=["tracks", "mixer"])`), matches names to instrument classes (Kick, Snare, Overheads, Bass, Guitars, Keys, Lead Vocal), and calls `live_update_track(track_index=..., gain_db=..., pan=...)` based on empirical MixologyDB genre averages. Leaves 6 dB master headroom.

9. Genius Action: Instrument Parametric EQ Eight Carving (`live_carve_eq_eight`)
   - Injects surgical 4-band or 8-band parametric EQ curves directly into native Ableton **EQ Eight** on any track:
     - `device_name="EQ Eight"`
     - Kick: 50 Hz HP, 106 Hz punch (+3 dB), 446 Hz mud cut (-6.5 dB), 2.8 kHz beater click (+4 dB).
     - Snare: 114 Hz HP, 200 Hz body (+3 dB), 732 Hz boxiness notch (-8 dB, Q=5.8), 7 kHz sizzle (+5.5 dB).
     - Bass: 92 Hz reciprocal notch, 400 Hz growl peak (+4 dB), 1.8 kHz fret noise cut (-12 dB).
     - Lead Vocal: 114 Hz HP, 980 Hz nasal dip (-4 dB), 2.8 kHz harshness notch (-3.5 dB), 12 kHz air shelf (+4 dB).

10. Genius Action: Semantic "Mix Doctor" Critique (`live_mix_critique`)
    - Reads active faders, pans, sends, and meter levels via `live_read_track` and `live_read_meter`, evaluates them against the 2,177 MixologyDB listening panel critique rules, and diagnoses mix flaws with actionable corrective advice or 1-click fixes.

#### PART 4: Advanced LiveAPI, CV Tools & Remote Script Suite (Ziforge Parity)
Integrate advanced LiveAPI and CV Tools capabilities extracted from `ableton_liveapi_tools`:

11. Genius Action: Musical Parameter Randomizer (`live_randomize_device`)
    - Discovers device parameters via `live_read_track(track_index, include=["devices"])`.
    - Filters out discrete/stepped parameters (`is_quantized == False`), volume faders, and bypassed states.
    - Safely mutates continuous timbre/envelope parameters within musical bounds, with optional `amount` scaling (0.0 to 1.0).

12. Genius Action: Max for Live & CV Tools Dynamic Parameter Control (`live_control_cv_tools`)
    - Dynamic introspection of Max for Live devices (`MxDeviceMidi`, `MxDeviceAudio`).
    - Maps and sets parameters by display name (e.g. "Rate", "Depth", "Waveform", "Amount") without fragile hardcoded indices.
    - Pre-calibrated CV modulators: CV LFO, CV Shaper, and Envelope Follower routing.

13. Genius Action: Hardware MIDI Synth & CC Integration (`live_setup_hardware_synth`, `live_send_midi_cc`)
    - Automates hardware analog synth setup: instantiates External Instrument or MIDI track, routes output port/channel, and sends MIDI CC or Program Change messages for preset recall.

14. Genius Action: Native MIDI Clip Quantization (`live_quantize_clip`)
    - Direct 1-shot note quantization via `clip.quantize(grid, amount)`.
    - Supported divisions: `"1/4"`, `"1/8"`, `"1/16"`, `"1/32"`, `"1/8T"`, `"1/16T"` with adjustable swing strength (0.0–1.0).

15. Genius Action: Live 12 Parameter Display Value Introspection (`live_read_display_values`)
    - Uses Live 12's native `param.display_value` property to read human-formatted strings (`"-14.2 dB"`, `"440 Hz"`, `"1/16"`) instead of normalized float decimals.

16. Bridge Architecture: Dual-Engine Hybrid Remote Script Connector (`live_connect_remote_script`)
    - Connects to Python Remote Script (`AbletonMCP` on port 9877 or `ClaudeMCP_Remote` on port 9004) for programmatic browser loading (`browser.load_item()`) to instantiate third-party VSTs and user library devices on demand.

#### PART 5: AbletonMCP Extended Operations & Algorithmic Music Engine (`jpoindexter/ableton-mcp` Parity)
Integrate extended Live operations and algorithmic pattern tools from `ableton_mcp_extended`:

17. Genius Action: Retrospective Capture MIDI (`live_capture_midi`)
    - Recovers unrecorded MIDI improvisation from Live 12's internal retrospective buffer via `song.capture_midi()`.
    - Automatically creates a new clip on the active track with detected tempo and cadence.

18. Genius Action: Arrangement Timeline Locators & Cue Points (`live_create_locator`, `live_jump_to_locator`, `live_get_locators`)
    - Creates, lists, and navigates cue markers (Intro, Verse, Chorus, Bridge, Drop, Outro) along the linear Arrangement timeline.

19. Genius Action: Drum Rack 128-Pad Mixer & Pad Mute/Solo (`live_get_drum_rack_pads`, `live_set_drum_pad_mute`, `live_set_drum_pad_solo`)
    - Inspects active pad samples across all 128 notes and performs surgical pad-level mute/solo during song sections.

20. Genius Action: Audio Clip Warp Mode & Generative Follow Actions (`live_set_clip_warp`, `live_set_clip_follow_action`)
    - Configures time-stretching algorithms (`Beats`, `Complex Pro`) and builds probabilistic looping follow actions (`Next`, `Random`, `Play Again`).

21. Genius Action: Device Chain Re-Ordering (`live_move_device`, `live_move_device_left`, `live_move_device_right`)
    - Dynamically moves audio effects along the track signal chain (`Track.move_device(from_index, to_index)`).

22. Genius Action: Session Safety & Panic Resets (`live_reset_mix_states`)
    - Batch restores audio playback by executing `unsolo_all()`, `unmute_all()`, `unarm_all()` in one atomic command.

23. Genius Action: Algorithmic Genre Grooves & Micro-Timing Humanizer (`live_generate_drum_pattern`, `live_generate_bassline`, `live_humanize_clip`)
    - Generates 8 drum styles (House, Trap, D&B, Funk, Jazz), 6 bassline styles, 13 scale modes, and applies subtle Gaussian timing/velocity jitter.

24. Architectural Integration: Python TCP Client Connector (`app/helper.py` -> `localhost:9877`)
    - Lightweight socket connector in `helper.py` sending `{"type": "<command>", "params": {...}}` directly to the installed `AbletonMCP` remote script.

#### PART 6: Native Sound Similarity Search & Advanced Live Execution (`bschoepke/ableton-live-mcp` Parity)
Integrate reverse-engineered Live 12 sound similarity and arbitrary Python execution:

25. Genius Action: Local Sound Similarity Search (`live_find_similar_sounds`)
    - Reads `%LOCALAPPDATA%\Ableton\Live Database\Live-files-12300.db` directly in Python.
    - Decodes 32-bit float neural audio feature vectors and computes cosine distance.
    - Recommends or swaps similar kicks, snares, percussion, or samples in milliseconds with zero cloud API overhead.

26. Genius Action: Arbitrary Live Python Execution (`live_exec_python`, `live_eval_python`)
    - Provides the ultimate escape hatch: executes arbitrary multi-line Python code directly on Live's main thread inside Live's interpreter.
    - Inspects and manipulates un-exposed LOM properties on demand.

27. Genius Action: Session-to-Arrangement Sequencer (`live_stamp_session_to_arrangement`)
    - Duplicates a Session clip slot into an Arrangement timeline track at a specified bar number to automatically sequence songs.

28. Genius Action: Clip Parameter & Velocity Envelopes (`live_draw_clip_envelope`, `live_clip_velocity_envelope`)
    - Reads and writes breakpoint automation curves and maps velocity dynamics to automation.

29. Genius Action: Real-Time Property Observers & Event Queue (`live_observe_property`, `live_drain_events`)
    - Attaches asynchronous property listeners to LOM objects (`tempo`, `is_playing`, faders) and reads captured events from a ring buffer.

30. Genius Action: Audio Signal Tapping & Spectrogram Telemetry (`AgentAudioTap.amxd`)
    - Taps live audio from any channel, computes FFT bins, and renders visual spectrograms for multimodal LLM analysis.

#### PART 7: ASCII Grid Notation, Snapshot LERP Morphing & Algorithmic Generators (`hidingwill/AbletonBridge` Parity)
Integrate the breakthrough token-efficient notation, device morphing, and algorithmic generators:

31. Genius Action: ASCII Grid Notation Compiler (`live_grid_to_clip`)
    - Compiles concise ASCII drum/synth tabs (e.g. `KK|o---o---|`, `SN|----o---|`, `HC|x-x-x-x-|`) directly into Live MIDI clips on the ticked track.
    - Uses 80% fewer LLM tokens than raw JSON note arrays and creates clips in a single turn.

32. Genius Action: MIDI Clip ASCII Visualizer (`live_clip_to_grid`)
    - Reads any active MIDI clip via `live_read_clip` and renders it back to an ASCII grid tab directly in chat for instant visual inspection of rhythms and melodies.

33. Genius Action: Device Preset Snapshotting & LERP Morphing (`live_snapshot_device`, `live_morph_snapshots`)
    - `live_snapshot_device`: Captures the complete parameter map of any active native or VST device into a named JSON snapshot.
    - `live_morph_snapshots`: Applies Linear Interpolation (LERP) between two snapshots across a user-specified morph percentage (0.0 to 1.0), enabling smooth sound design transitions and A/B crossfading.

34. Genius Action: Algorithmic Euclidean & Polyrhythm Generators (`live_generate_euclidean`, `live_generate_polyrhythm`)
    - `live_generate_euclidean`: Implements the Bjorklund algorithm to distribute k pulses across n steps (e.g. Cuban cinquillo 5/16, tresillo 3/8, bossa nova).
    - `live_generate_polyrhythm`: Generates dual metric counterpoint (e.g. 3 against 4, 5 against 4) directly onto separate drum rack pads or tracks.

35. Genius Action: Sidechain Compression Routing (`live_set_sidechain`)
    - Programmatically configures native Ableton **Compressor** sidechain routing (`routing_type`, `routing_channel`, `gain`, `mix`) to duck Bass or Pads against the Kick track.

36. Genius Action: Compound 1-Shot Workflows (`live_create_instrument_track_workflow`, `live_setup_send_return_chain`)
    - Combines multi-step manual tasks into single atomic macros: creates MIDI track, inserts instrument, loads preset, adds utility and EQ Eight, and assigns standard macro mappings in 1 call.

#### PART 8: AbletonOSC Remote Script Suite, Bulk Session Dump & MIDI Mapping (`ideoforms/AbletonOSC` Parity)
Integrate root application-level OSC control running without Max for Live dependencies:

37. Genius Action: 1-Shot Project Structural Dump (`live_export_project_structure`)
    - Calls `/live/song/export/structure` to write a comprehensive JSON snapshot (`abletonosc-structure.json`) of all tracks, groups, clips, devices, and parameter states in <5ms.
    - Loads the resulting JSON in Python for instant full-session awareness without hundreds of sequential LOM queries.

38. Genius Action: Bulk Multi-Track State Query (`live_bulk_track_query`)
    - Sends `/live/song/get/track_data` to fetch names, volumes, pans, mute states, and clip lengths for up to 32 tracks in a single UDP packet.

39. Genius Action: Track Bus & Sidechain I/O Routing (`live_route_track_io`)
    - Configures track input/output routing (`/live/track/set/input_routing_type`, `output_routing_type`, and channels) to build submix busses (e.g. Drum Bus, Vocal Stem) and sidechain feeds programmatically.

40. Genius Action: Dynamic Hardware MIDI CC Mapping (`live_map_parameter_to_cc`)
    - Calls `/live/midimap/map_cc` to dynamically bind any device parameter `(track, device, param)` to a physical/virtual MIDI `(channel, cc)` and rebuilds Live's MIDI map. Perfect for Novation Launchkey MK4 custom modes.

41. Genius Action: 5-Tuple OSC Clip Notes Engine (`live_osc_batch_clip_notes`)
    - Reads, adds, and removes notes formatted as 5-tuples `[pitch, start_time, duration, velocity, mute]` via `/live/clip/get/notes`, `/live/clip/add/notes`, and `/live/clip/remove/notes` with pitch/time window bounding.

42. Genius Action: Real-Time Beat Clock Synchronizer (`live_sync_beat_listener`)
    - Starts or stops listening to `/live/song/start_listen/beat` to receive beat clock events locked to Live's playback transport.

43. Genius Action: Semantic Arrangement Locator Jump (`live_jump_to_named_cue`)
    - Executes `/live/song/cue_point/jump` with cue name strings (e.g. "Intro", "Drop", "Chorus") for instant arrangement navigation.

#### PART 9: PyLive Python Client SDK, ASCII Tree Dumper & Generative Clip Walking (`ideoforms/pylive` Parity)
Integrate high-level object-oriented Python LOM bindings and generative algorithms into Engine 3:

44. Genius Action: ASCII Session Tree Generator (`live_pylive_dump_tree`)
    - Executes `set.dump()` to return a clean, visual ASCII tree hierarchy of all tracks, groups, active clips, and devices directly in chat (under 80 tokens).

45. Genius Action: Semantic Object Resolver (`live_pylive_get_by_name`)
    - Resolves tracks, groups, or devices by human name (e.g. `get_track_named("Lead Vocal")`) and returns their volume, pan, device list, and active clips without index errors.

46. Genius Action: Autonomous Clip Walker (`live_pylive_walk_clips`)
    - Algorithmic generative clip walker that stochastically or sequentially navigates through populated clips on a target track or group, locked to beat boundaries.

47. Genius Action: Continuous Tempo Shaper (`live_pylive_modulate_tempo`)
    - Applies real-time mathematical curves (sinusoidal rubato, exponential build, gradual ritardando) to Live's tempo over a specified duration.

48. Genius Action: Safe Device Parameter Randomizer (`live_pylive_randomize_device_safe`)
    - Musical device parameter mutator that sweeps continuous parameters across their defined min/max range while preserving `Device On`, power, and discrete bypass switches.

49. Host Tool: Session State Disk Caching (`live_pylive_cache_session_state`)
    - Serializes the active `live.Set` Python instance into a local pickle cache in `%APPDATA%\Live Actions\cache\` for instant offline project inspection.

#### PART 10: LiveRPyC Direct Memory Proxy, Cross-Process Listeners & Zero-Protocol LOM Control (`lucianoiam/live_rpyc` Parity)
Integrate direct memory proxying and transparent C++ LiveAPI dereferencing into Engine 2 & 3:

50. Genius Action: Direct Python LOM Evaluator (`live_rpyc_eval_lom`)
    - Evaluates arbitrary Python expressions directly against the live `song` proxy (e.g. `[t.name for t in song.tracks if t.mute]`) and returns native primitives in <1ms without string serialization.

51. Genius Action: Zero-Latency Proxy Track Control (`live_rpyc_direct_track_control`)
    - Directly mutates track faders, pans, sends, mute, solo, and arm using native C++ object properties (`track.mixer_device.volume.value = 0.85`) across TCP 17744.

52. Genius Action: Cross-Process Event Listener (`live_rpyc_bind_listener`)
    - Uses `lom_observer_helper.bind()` to register external Python callbacks that fire in real time whenever Live parameters, tempo, or playhead positions change.

53. Genius Action: Deep Device & Rack Introspector (`live_rpyc_deep_device_inspect`)
    - Recursively traverses complex nested devices, Audio Effect Racks, Drum Racks, and return chains using native Python object reflection (`dir()`, `getattr()`).

54. Genius Action: Native C++ MIDI Note Injector (`live_rpyc_note_matrix`)
    - Instantiates `Live.Clip.MidiNoteSpecification` directly on Live's heap and injects batches of notes via `clip.add_new_notes()` with zero JSON conversion overhead.

55. Genius Action: Multi-Track State Scraper (`live_rpyc_batch_query`)
    - Evaluates multi-track queries across 50+ tracks in a single local Python loop over the proxy connection, retrieving complete project states in 2ms.

#### PART 11: Ableton Live API Stub, Pre-Execution Validator & Schema Engine (`cylab/AbletonLive-API-Stub` Parity)
Integrate static pre-execution validation and authoritative LOM permission verification into the Static Verification Tier (Tier 0):

56. Genius Action: Pre-Execution LOM Validator (`live_validate_lom_call`)
    - Statically verifies whether a target class (e.g. `Song`, `Track`, `Clip`, `DeviceParameter`) possesses the requested method or attribute, validating parameter names and types before sending calls to Live.

57. Genius Action: Authoritative LOM Docstring & Permission Lookup (`live_query_lom_docstring`)
    - Inspects Boost.Python docstrings to determine whether properties have "Read, write, and listen access", "Get/Set", or "Read-only" permissions.

58. Genius Action: Listenable Event Property Finder (`live_find_listenable_properties`)
    - Identifies all attributes on an object class that support `add_*_listener` callbacks, preventing invalid listener registrations.

59. Genius Action: Validated API Enum Mapper (`live_get_api_enums`)
    - Translates user-facing string names (e.g. "Complex Pro", "Beats", "1/16") to validated integer enums for `WarpMode`, `Quantization`, and `DeviceType`.

60. Genius Action: Canonical LOM Path Resolver (`live_resolve_canonical_path`)
    - Validates canonical path strings (e.g. `live_set tracks 0 mixer_device volume`) and checks each path segment against stub class definitions.

61. Genius Action: Offline Type Stub Installer (`live_install_offline_stubs`)
    - Installs or links `Live___init__.py` as a pure-Python `Live` package into the active virtual environment to enable `import Live` in external IDEs and test suites.

#### PART 12: Max 9 LOM, Live 12 Flagship Devices, Tuning Systems & Native Ableton DSP Engine
Integrate deep Live 12 device specialization, microtonality, take lane comping, and native `abl.*` DSP specs into Genius:

62. Genius Action: Live Status Bar Notification (`live_show_status_message`)
    - Writes non-intrusive operational status messages directly to Ableton Live's bottom-left status bar using `Application.show_on_the_fly_message()`.

63. Genius Action: Microtonal Tuning System Manager (`live_tuning_system`)
    - Inspects and modifies Live 12's native microtonal tuning parameters (`reference_pitch`, `lowest_key`, `pitch_names`, `scale_intervals`).

64. Genius Action: Take Lane & Comping Manager (`live_take_lane_control`)
    - Programmatically inspects, mutes, solos, and promotes audio and MIDI take lanes (`track.take_lanes`) for vocal and instrumental comping.

65. Genius Action: Live 12 Flagship Synth Specialist (`live_meld_roar_drift_control`)
    - Exposes high-level macro parameters for Live 12's `Meld` (bi-timbral macro synth), `Roar` (multi-stage saturation & feedback matrix), and `Drift` (analog drift & stereo spread).

66. Genius Action: Live 11 to 12 Runtime Member Verifier (`live_verify_runtime_member`)
    - Validates proposed LOM calls against the 1,427 added and 84 removed member database to prevent version mismatches.

67. Genius Action: Native Ableton DSP Catalog (`live_query_abl_dsp_specs`)
    - Inspects exact parameter, inlet, and outlet specifications for the 74 native `abl.*` Live DSP algorithms (EQ Eight, Delay, Compressor) in Max 9.

68. Genius Action: Node for Max & V8 Dictionary Bridge (`live_node_for_max_bridge`)
    - Uses `max-api` (`setDict`, `getDict`, `addHandler`) to pass large JSON dictionaries asynchronously between Node.js and Max for Live without audio dropouts.

#### PART 13: Cycling '74 Max 1,805-Object Engine, MC Multi-Channel Polyphony & Gen~ DSP Architecture
Integrate full-spectrum Max/MSP, MC multi-channel polyphony, Gen~ low-level machine code DSP, and Jitter audio-reactive visuals into Genius:

69. Genius Action: Max 1,805-Object Specification Lookup (`live_max_object_lookup`)
    - Statically validates any of the 1,805 Cycling '74 objects (inlets, outlets, package, category, type description) to prevent hallucinated object names during patch generation.

70. Genius Action: MC Multi-Channel Polyphony & Voice Spreader (`live_mc_voice_spreader`)
    - Constructs 16/32/64-channel parallel audio graphs (`mc.cycle~`, `mc.svf~`, `mc.spread`, `mc.stereo~`) for unison supersaws and spatial panning without subpatches.

71. Genius Action: Gen~ Sample-Accurate DSP Builder (`live_gen_dsp_builder`)
    - Emits JIT-compiled C++ machine code scripts for the Gen~ `codebox` operator (diode ladder filters, tape saturation, physical modeling resonators).

72. Genius Action: Programmatic M4L Patcher Synthesizer (`live_m4l_patch_synthesizer`)
    - Generates complete Max patcher JSON graphs and JavaScript automation scripts (`this.patcher.newdefault()`, `connect()`) to wire custom M4L devices dynamically.

73. Genius Action: Jitter Audio-Reactive Visualizer Builder (`live_jitter_audio_visualizer`)
    - Generates real-time 3D OpenGL and GLSL shader graphs (`jit.world`, `jit.gl.gridshape`, `jit.gl.pix`) reacting to Live audio levels and MIDI events.

#### PART 14: Live 12 Remote Scripts v3 Framework, Novation Launchkey MK4 & _MxDCore Bridge Engine
Integrate deep hardware controller profiling, Novation Launchkey MK4 Sysex control, Ableton v3 components, and `_MxDCore` bridge introspection into Genius:

74. Genius Action: Novation Launchkey MK4 Sysex Control (`live_launchkey_mk4_sysex`)
    - Generates and dispatches exact Sysex strings to switch Launchkey MK4 between DAW, Standalone, and Programmer modes, and controls pad RGB velocity colors.

75. Genius Action: Hardware Controller Profile Inspector (`live_hardware_controller_inspect`)
    - Retrieves layout and mapping specifications for any of the 148 documented MIDI controllers (Push 3, Launchkey MK4, APC64, KeyLab, FaderPort).

76. Genius Action: Ableton v3 Component Factory (`live_v3_component_builder`)
    - Emits verified modern `ableton.v3` Python code to add advanced features (`AutoArmComponent`, `ActiveParameterComponent`, `ViewControlComponent`).

77. Genius Action: Max for Live `_MxDCore` Bridge Inspector (`live_mxdcore_inspect`)
    - Inspects internal object ID resolution, dispatch queues, and listener aggregation mechanics in Live's Max for Live bridge.

78. Genius Action: Controller OLED Screen Formatter (`live_format_controller_display`)
    - Formats track names, parameter names, and dB values with optimal truncation and unit suffixes for hardware OLED and LCD screens.

79. Genius Action: Remote Script Cookbook Recipe Synthesizer (`live_script_recipe_builder`)
    - Generates verified code patterns for raw MIDI message interception (`receive_midi`), button action callbacks (`button.add_value_listener`), relative encoder modes (`relative_two_compliment`), and safe listener teardown in `disconnect()`.

80. Genius Action: Hierarchical LOM Map Navigator (`live_lom_map_navigator`)
    - Queries the comprehensive 100 KB Live 12 LOM hierarchy tree to resolve parent-child paths and canonical string addressing (`live_set tracks 0 ...`).

#### PART 15: Hardware Feedback, Dynamic Modes, Routing & Diagnostics (Actions 81–90)
- **Action 81: Hardware LED Palette & Pad Colorizer (`live_hardware_led_palette`)**
  - Translates standard semantic color names (`red`, `green_half`, `amber_pulse`, `blue_blink`, `ocean`) into the exact MIDI velocity byte required by specific hardware controllers (Launchpad, Launchkey MK4, APC64, APC mini mk2, PreSonus ATOM, ATOM SQ, Akai Force/MPC, KeyLab mk3, Move, Push 1/2/3).
- **Action 82: Dynamic Controller Layer & Modes Architect (`live_modes_layer_architect`)**
  - Generates production-grade Python code for multi-layer hardware controller behavior using `ModesComponent` and `Layer`. Automatically hooks listener switches and ensures inactive modes cleanly release physical controls to avoid conflict bugs.
- **Action 83: MIDI Message Flow & Event Interceptor (`live_midi_flow_analyzer`)**
  - Designs and validates custom MIDI routing tables between physical controllers, Remote Scripts, and Live tracks. Determines whether incoming CCs or notes should be swallowed for DAW navigation, forwarded to Live for recording (`forward_to_live`), or transformed into MPE data.
- **Action 84: Live 12 CC Control Hardware Mapper (`live_cc_control_manager`)**
  - Configures Live 12's new `CC Control` MIDI device parameters (0–127), bipolar/unipolar ranges, parameter labels, and automation routing for external hardware synthesizers, Eurorack MIDI-to-CV modules, and outboard gear.
- **Action 85: Direct Automation Curve Generator (`live_automation_curve_generator`)**
  - Programmatically draws smooth or stepped parameter automation curves directly inside MIDI or Audio clips using native Live 12 `AutomationEnvelope` step insertion (exponential filter sweeps, 4-on-the-floor sidechain pumping, panning LFOs, and pitch ramps).
- **Action 86: Programmatic Device Chain Mutator (`live_device_chain_mutator`)**
  - Duplicates or inserts native Ableton devices and plugin chains on any track while preserving or morphing parameter settings, enabling one-click parallel processing chains and sound doubling.
- **Action 87: AI Song Form & Structure Arranger (`live_ai_song_arranger`)**
  - Builds complete multi-track song arrangements in Session or Arrangement view from genre prompts (Intro, Verse, Pre-Chorus, Chorus, Breakdown, Drop, Outro), creating named/color-coded scenes and setting scene-launch tempo automations.
- **Action 88: Algorithmic Melody & Rhythmic Evolver (`live_ai_melody_evolver`)**
  - Takes existing MIDI clips and produces variations via inversion, retrograde, rhythmic augmentation/diminution, velocity humanization, and scale snapping to the active Live 12 scale/tuning.
- **Action 89: Live Log & Script Crash Diagnostician (`live_log_error_diagnostician`)**
  - Tails and parses Ableton Live's `Log.txt` in real time, isolating Python tracebacks, syntax errors, and missing listener unhooking (`add_*_listener` without `remove_*_listener` in `disconnect()`).
- **Action 90: Max 9 M4L Dynamic Dictionary & Web Bridge (`live_m4l_dictionary_bridge`)**
  - Formats, validates, and routes structured JSON data packets between HTML/React/Canvas web interfaces running in Max for Live's `jweb` browser and Live's native DSP/LOM backend.

#### PART 16: Live 12 Flagship Sound Design, MPE Microtonality, Drum Grooves & Stems (Actions 91–115)
- **Action 91: Live 12 Roar Multi-Stage Saturation Architect (`live_roar_multistage_architect`)**
  - Programs Roar's routing topologies (Single, Serial, Parallel, Multi-band, Mid-Side, Feedback), dialing in drive, tone, filter stages, bias, and envelope followers.
- **Action 92: Live 12 Meld Bi-Timbral Macro Sculptor (`live_meld_macro_sculptor`)**
  - Configures dual macro-oscillator engines from Meld's 24 algorithmic models (Rain, Swarm, Tangle, Fold), assigns cross-modulation, and routes the macro filter matrices.
- **Action 93: Live 12 Drift Analog Voice Designer (`live_drift_analog_voice_designer`)**
  - Dials in vintage analog drift variance, stereo voice spread, cycling envelope shapes, touch-strip modulation, and MPE slide curves for the Drift synth.
- **Action 94: Dynamic Envelope Follower & LFO Modulator (`live_envelope_follower_modulator`)**
  - Binds native M4L / Live 12 Envelope Followers or LFOs to arbitrary device parameters (e.g., sidechaining snare transients to reverb wet/dry).
- **Action 95: Live Shaper Multi-Breakpoint Designer (`live_shaper_multi_breakpoint_designer`)**
  - Generates multi-segment breakpoint curves for the native Live Shaper modulation device (exponential curves, glitch patterns, polyrhythmic step shapes).
- **Action 96: MPE Per-Note Expression Painter (`live_mpe_expression_painter`)**
  - Injects per-note MPE curves—per-note pitch bend, polyphonic pressure/aftertouch, and slide (timbre)—into individual notes within a Live 12 MIDI clip.
- **Action 97: Scala File Parser & Microtonal Tuning Mapper (`live_scala_tuning_importer`)**
  - Parses `.scl` and `.kbm` scale files and maps them directly into Live 12's `TuningSystem` LOM to apply custom historical or non-Western tunings.
- **Action 98: Microtonal Chord Voicing Engine (`live_microtonal_chord_voicing`)**
  - Calculates harmonic voicings using microtonal intervals, cent offsets, 24-TET quarter tones, or Bohlen-Pierce ratios.
- **Action 99: Polyphonic Aftertouch & Pressure Generator (`live_polyphonic_aftertouch_generator`)**
  - Generates independent key pressure events tailored for expressive synth pads and strings.
- **Action 100: Acoustic Strum & Pluck Humanizer (`live_mpe_strum_humanizer`)**
  - Introduces micro-time strum delays (5–25 ms) and per-note velocity/pressure gradients across polyphonic chords to emulate realistic acoustic or flamenco guitar strumming.
- **Action 101: Drum Rack Choke & Mute Group Matrix (`live_drum_rack_choke_matrix`)**
  - Inspects and configures choke groups across all 128 Drum Rack pads (e.g., assigning open/closed hi-hats or mute groups to prevent bleeding).
- **Action 102: Simpler Slice Mode Configurator & MIDI Transcriber (`live_simpler_slice_transcriber`)**
  - Configures Simpler's Slicing mode (transient, beat, region, or manual slice points) and automatically generates slice-trigger MIDI clips.
- **Action 103: Clip Groove Extractor & Swing Quantizer (`live_groove_pool_extractor`)**
  - Extracts groove timing and velocity templates from audio or MIDI clips, loads them into Live's Groove Pool, and applies them with adjustable Quantize/Timing/Velocity/Random percentages.
- **Action 104: Multi-Voice Polyrhythmic Euclidean Generator (`live_polyrhythm_euclidean_matrix`)**
  - Interlaces multiple simultaneous Euclidean rhythms across separate drum voices (e.g., 5/16 kick against 7/16 hi-hat against 3/16 rimshot) inside a single Drum Rack clip.
- **Action 105: Dynamic Drum Velocity Layer Humanizer (`live_drum_velocity_layer_humanizer`)**
  - Rewrites drum clip velocities to follow acoustic drummer dynamics (ghost notes at 25–40 vel, backbeats at 105–118 vel, hi-hat velocity accents alternating 80/55/90/60).
- **Action 106: Stem Bouncing & Mixdown Prepper (`live_stem_export_prepper`)**
  - Normalizes track names, color codes stems by bus, resets master fader to 0 dB, verifies headroom, and mutes disabled tracks.
- **Action 107: Arrangement Locator & Song Section Marker (`live_arrangement_marker_generator`)**
  - Places Arrangement View locators/cue points with custom names (Intro, Verse, Chorus, Bridge, Drop, Outro) and bar positions based on the project structure.
- **Action 108: DJ Crossfader Assigner & Curve Controller (`live_crossfader_assigner`)**
  - Configures track A/B crossfader assignments (`mixer_device.crossfade_assign`) and automation curves for DJ transitions or live performance.
- **Action 109: Send/Return Bus Matrix Balancer (`live_send_return_matrix_balancer`)**
  - Audits send levels across all tracks to verify gain staging on reverb and delay returns, preventing master bus clipping or muddy sub frequencies.
- **Action 110: CPU Load Auditor & Track Freeze Planner (`live_track_freeze_flatten_planner`)**
  - Audits CPU load across tracks, identifies heavy VST/DSP chains, and prepares an automated freeze/flatten plan for high-latency tracks.
- **Action 111: Hardware Controller Parameter Bank Formatter (`live_push_screen_bank_formatter`)**
  - Formats parameter bank layouts (`live.banks`) for Push 2/3 and 8-encoder controllers, organizing custom macro names and parameter order for 3rd-party VSTs.
- **Action 112: Jog-Wheel Scrubbing & Beat Jumper (`live_transport_scrub_controller`)**
  - Implements dynamic jog-wheel scrubbing, beat jumping, and loop point shifting for live DJing and arrangement navigation.
- **Action 113: Smooth Tempo Ramp & Transition Builder (`live_tempo_automation_ramper`)**
  - Creates gradual tempo accelerando or ritardando between scenes or timeline sections with smooth Bezier or linear interpolation.
- **Action 114: Probabilistic Clip Follow Action Matrix (`live_clip_follow_action_matrix`)**
  - Programs complex probabilistic Follow Actions (e.g., 70% play next clip, 20% jump to slot 4, 10% stop) for generative, never-repeating live performances.
- **Action 115: Scene Tempo & Time Signature Automator (`live_scene_tempo_signature_tagger`)**
  - Tags Session scenes with dedicated tempo and time-signature identifiers (e.g., `Scene 1 [128 BPM] [4/4]`, `Scene 5 [85 BPM] [7/8]`) to automate transport changes on scene fire.

#### PART 17: Real LOM Audio Warping, Monitoring, Routing & Metering (Actions 116–125)
- **Action 116: Audio Clip Warp Mode & Complex Pro Formant Shifter (`live_audio_warp_engine`)**
  - Configures audio clip warp modes (`Beats`, `Tones`, `Texture`, `Re-Pitch`, `Complex`, `Complex Pro`) and tunes formant preservation and envelope parameters for pitch-shifted vocals and instruments.
- **Action 117: Beats Granulation & Transient Loop Mode Optimizer (`live_beats_transient_engine`)**
  - Controls rhythmic slice decay envelopes (`beats_transient_envelope`) and transient loop modes (`Off`, `Forward`, `Alternate`) in Beats warp mode for tight gating and stutter effects.
- **Action 118: Texture & Tones Granular Flux Controller (`live_granular_texture_flux`)**
  - Modulates grain size and randomness (`texture_flux`, `texture_grain_size`, `tones_grain_size`) on time-stretched audio clips to create ambient granular drone beds and cloud textures.
- **Action 119: Track Input Monitoring State Switcher (`live_monitoring_state_control`)**
  - Switches track monitoring modes programmatically (`In`, `Auto`, `Off`), setting live vocal/mic inputs to `In` during rehearsal and `Auto` during punch-in tracking.
- **Action 120: Inter-Track Audio & MIDI Sub-Routing Matrix (`live_routing_matrix_config`)**
  - Configures internal track-to-track routing (`input_routing_type`, `output_routing_type`, `input_routing_channel`, `output_routing_channel`), enabling arpeggiator-to-synth feeds and drum sub-group stems.
- **Action 121: Hardware Peak & RMS CPU Usage Monitor (`live_cpu_meter_inspector`)**
  - Queries Live's actual DSP process load metrics (`average_process_usage`, `peak_process_usage`) in real time to alert the producer before audio dropouts occur.
- **Action 122: Arrangement Cue Point Locator Navigator (`live_cue_point_navigator`)**
  - Catalogs all arrangement markers/cue points (`cue_points`), retrieves their exact beat positions, and jumps the arrangement playhead directly to named song sections.
- ~~Action 123: Track Freeze & Thaw State Controller (`live_track_freeze_control`)~~ -- **proven impossible (v1.0.39 audit)**:
  `can_be_frozen` / `is_frozen` are absent from `Track` in the Live 12.3.6 LOM reference (`app/lom_surface.json`).
  There is no freeze/flatten member on `Track` at all -- see the "Explicitly out of scope" section of
  `docs/plans/v1.0.39-lom-truth-table-and-verified-actions.md`.
- **Action 124: Clip RAM Mode & Pitch Fine/Coarse Detuner (`live_clip_pitch_ram_control`)**
  - Toggles RAM buffer loading (`ram_mode`) for zero-latency sample playback and sets microtonal cent fine-tuning (-50 to +50 cents) and semitone transpositions (-48 to +48 st).
- **Action 125: Metronome Count-In Duration & Transport Nudge Engine (`live_metronome_nudge_control`)**
  - Programs count-in duration (`count_in_duration`) for recording takes and applies transport tempo nudging (`nudge_up`, `nudge_down`) for manual beatmatching against external turntables.

#### PART 18: Browser Exploration, Drum Pad Manipulation & GUI Viewport Automation (Actions 126–140)
- **Action 126: User Library & Core Packs Browser Explorer (`live_browser_tree_query`)**
  - Traverses Ableton's internal Browser hierarchy (`user_library`, `packs`, `sounds`, `instruments`, `audio_effects`) to discover installed sample packs, user presets, and native instruments.
- **Action 127: Hotswap Target Discovery & Trigger (`live_hotswap_target_control`)**
  - Queries the currently active hotswap target (`hotswap_target`), allowing intelligent sound browsing targeted directly to the active Drum Rack pad or Simpler device.
- **Action 128: Drum Rack Pad Duplicator & Pad Copier (`live_drum_pad_copier`)**
  - Programmatically duplicates drum pads (including all nested Simpler devices, samplers, and effect inserts) from one pad note to another using `copy_pad(source_pad, target_pad)`.
- **Action 129: Native Dialog Message Interceptor & Auto-Dismiss (`live_dialog_message_handler`)**
  - Detects modal dialog boxes in Live (`current_dialog_message`, `open_dialog_count`), reads dialog text, and programmatically clicks OK/Cancel (`press_current_dialog_button`).
- **Action 130: GUI View Visibility & Splitter Focus Toggler (`live_gui_view_visibility`)**
  - Toggles GUI sub-views (`Detail/Clip`, `Detail/Device`, `Browser`, `In/Out`, `Returns`, `Mixer`) to optimize screen real estate during production.
- **Action 131: GUI Viewport Zoom & Smooth Scroll Engine (`live_viewport_zoom_scroll`)**
  - Programmatically scrolls the Arrangement timeline or Session matrix up/down/left/right and controls GUI zoom levels (`zoom_view`, `scroll_view`).
- **Action 132: Song Loop Marker Window & Punch Region Setters (`live_song_loop_region_control`)**
  - Programmatically positions the Arrangement loop brace (`loop_start`, `loop_length`, `loop`) and enables timeline loop playback.
- **Action 133: Groove Pool Global Amount & Timing Base Tweaker (`live_groove_amount_control`)**
  - Controls the global master Groove Pool slider (`groove_amount` 0.0 to 1.0) to scale the intensity of swing across all clips in the project simultaneously.
- **Action 134: Clip Trigger Quantization & Launch Legato Configurator (`live_clip_trigger_quantization`)**
  - Sets global or per-clip launch quantization (`clip_trigger_quantization`, `launch_quantization`: None, 8 Bars to 1/32) and Legato launch mode.
- **Action 135: Simpler Slicing Playback Mode & Beat Division Engine (`live_simpler_playback_engine`)**
  - Toggles Simpler between Classic, One-Shot, and Slicing modes (`playback_mode`), configuring beat divisions (`slicing_beat_division`) and pad trigger assignments.
- **Action 136: MIDI Note Probability & Velocity Deviation Painter (`live_note_probability_humanizer`)**
  - Injects note firing probability (0.0 to 1.0) and velocity deviation ranges into individual MIDI notes using Live's native `apply_note_modifications` API for generative patterns.
- **Action 137: Track Arm & Solo Exclusivity Mode Switcher (`live_exclusive_arm_solo_control`)**
  - Toggles whether arming or soloing a track automatically un-arms or un-solos other tracks (`exclusive_arm`, `exclusive_solo`), essential for live multi-mic tracking.
- **Action 138: Clip Selected Notes Transformer & Range Inverter (`live_clip_selected_notes_transform`)**
  - Modifies only the currently highlighted notes within the Ableton clip detail editor (`get_selected_notes`, `replace_selected_notes`), enabling selective chord extension inversion.
- **Action 139: Song Appointed Device & Floating Window Revealer (`live_appointed_device_control`)**
  - Sets which device has keyboard focus (`appointed_device`) and opens/closes floating VST/AU plugin interface windows.
- **Action 140: Real-Time Audio Clip Scrubbing & Timeline Cue Auditioner (`live_audio_clip_scrub_audition`)**
  - Programmatically scrubs and auditions short slices of audio from any point in an audio clip (`Clip.scrub(time, duration)`) without altering the global transport playhead.

#### PART 19: Registration & Verification
- Register all new host runners in `HOST_TOOLS` in `app/helper.py`.
- Register all new genius tools in `LIVE_TOOLS` and `call_live_tool()` in `app/genius_client.py`.
- Connect all fourteen datasets (`vital_synth_headless_lab`, `ableton-racks-labeled`, `mixology_db`, `ableton_liveapi_tools`, `ableton_mcp_extended`, `ableton_live_mcp_bschoepke`, `ableton_bridge_hidingwill`, `abletonosc_ideoforms`, `pylive_ideoforms`, `live_rpyc_lucianoiam`, `ableton_api_stub_cylab`, `ableton_ai_max9_lom_training`, `cycling74_max_reference`, and `live_12_remote_scripts_reference`) to the Genius system knowledgebase.
- Follow Step 3 & 4: Determine semver bump from git tags (`git describe --tags --abbrev=0`), update Implementation Plan, append new entry to `App Changes Tracker.html`, commit, tag `vX.Y.Z`, push to GitHub, and clean up session notes.
```

---

## 2. Complete Capabilities Matrix Across All 18 Pillars

| Pillar | Focus Domain | Primary Capabilities & Tools |
| :--- | :--- | :--- |
| **1. Vital Host Tools** | Pure Python Offline Host | CLI sound design, wavetable morphing, preset generation (`vital_create_preset`, `vital_render_audio`, `vital_wavetable_inject`, etc.) |
| **2. Producer Pal Genius Native Racks** | AI Agent Tool Calling | Macro discovery, parameter introspection, rack mapping (`live_read_device`, `live_update_device`, `live_create_device`) |
| **3. MixologyDB** | Mix Engineering Suite | 4-pass surgical gain staging, dynamic EQ ducking, harmonic saturation, limiter ceiling check |
| **4. Ziforge Parity** | Advanced LiveAPI & CV | Raw LOM execution, OSC parameter sweeps, CV modulation tools, Remote Script bridge |
| **5. AbletonMCP** | Algorithmic Music Engine | Multi-clip generation, chord progression resolver, Euclidean polyrhythms, scale snapping |
| **6. bschoepke MCP** | Sound Similarity Search | Neural embedding browser, sample similarity matching, auto-drum kit population |
| **7. hidingwill MCP** | ASCII Grid & Morphing | ASCII step-sequencer grids, multi-parameter snapshot LERP morphing, probabilistic gates |
| **8. AbletonOSC** | Remote Script OSC Suite | Bidirectional OSC listener daemon, bulk session JSON dumps, MIDI surface mapping |
| **9. PyLive SDK** | Live Object Model SDK | Live Python client, ASCII track/scene tree visualizer, generative clip walker |
| **10. LiveRPyC** | Zero-Protocol Memory Proxy | Direct memory introspection, synchronous RPC calls, low-latency parameter listening |
| **11. Ableton Live API Stub** | Pre-Execution LOM Validator | Offline type checking, signature lookup, permission checking, listenable property audit (`live_validate_lom_call`, `live_query_lom_docstring`, `live_find_listenable_properties`, `live_get_api_enums`, `live_resolve_canonical_path`, `live_install_offline_stubs`) |
| **12. Max 9 & Flagship DSP** | Modern Ableton Architecture | Status bar feedback (`live_show_status_message`), microtonal tuning (`live_tuning_system`), take lanes (`live_take_lane_control`), flagship sound design (`live_meld_roar_drift_control`), runtime verification (`live_verify_runtime_member`), native DSP catalog (`live_query_abl_dsp_specs`) |
| **13. Cycling '74 Max Engine** | Max 9 Engine & Multi-Channel | Node for Max bridge (`live_node_for_max_bridge`), 1,805-object catalog (`live_max_object_lookup`), MC polyphony (`live_mc_voice_spreader`), Gen~ sample-accurate DSP (`live_gen_dsp_builder`), programmatic M4L patcher synthesis (`live_m4l_patch_synthesizer`), Jitter audio visualizer (`live_jitter_audio_visualizer`) |
| **14. Remote Scripts v3 & MxDCore** | Hardware Scripts & LOM Navigation | Launchkey MK4 Sysex (`live_launchkey_mk4_sysex`), hardware profile inspector (`live_hardware_controller_inspect`), v3 component factory (`live_v3_component_builder`), MxDCore inspector (`live_mxdcore_inspect`), OLED formatter (`live_format_controller_display`), script cookbook builder (`live_script_recipe_builder`), LOM map navigator (`live_lom_map_navigator`) |
| **15. Hardware Feedback & Diagnostics** | LED Colors, Modes, Routing & Logs | Hardware LED palette (`live_hardware_led_palette`), dynamic modes architect (`live_modes_layer_architect`), MIDI flow analyzer (`live_midi_flow_analyzer`), CC Control manager (`live_cc_control_manager`), direct automation curve generator (`live_automation_curve_generator`), device chain mutator (`live_device_chain_mutator`), AI song arranger (`live_ai_song_arranger`), melody evolver (`live_ai_melody_evolver`), Live log crash diagnostician (`live_log_error_diagnostician`), M4L dynamic dictionary bridge (`live_m4l_dictionary_bridge`) |
| **16. Flagship Sound, MPE & Stems** | Roar/Meld, MPE, Grooves & Performance | Roar saturation architect (`live_roar_multistage_architect`), Meld macro sculptor (`live_meld_macro_sculptor`), Drift analog designer (`live_drift_analog_voice_designer`), envelope follower modulator (`live_envelope_follower_modulator`), Shaper breakpoint designer (`live_shaper_multi_breakpoint_designer`), MPE expression painter (`live_mpe_expression_painter`), Scala tuning importer (`live_scala_tuning_importer`), microtonal chords (`live_microtonal_chord_voicing`), poly aftertouch (`live_polyphonic_aftertouch_generator`), strum humanizer (`live_mpe_strum_humanizer`), drum choke matrix (`live_drum_rack_choke_matrix`), Simpler slice transcriber (`live_simpler_slice_transcriber`), groove extractor (`live_groove_pool_extractor`), polyrhythm matrix (`live_polyrhythm_euclidean_matrix`), drum velocity humanizer (`live_drum_velocity_layer_humanizer`), stem export prepper (`live_stem_export_prepper`), arrangement markers (`live_arrangement_marker_generator`), crossfader assigner (`live_crossfader_assigner`), send/return balancer (`live_send_return_matrix_balancer`), freeze/flatten planner (`live_track_freeze_flatten_planner`), Push bank formatter (`live_push_screen_bank_formatter`), transport scrub controller (`live_transport_scrub_controller`), tempo ramper (`live_tempo_automation_ramper`), follow action matrix (`live_clip_follow_action_matrix`), scene tempo tagger (`live_scene_tempo_signature_tagger`) |
| **17. Real LOM Audio Warping & Routing** | Formants, Granulation & Routing | Audio warp engine (`live_audio_warp_engine`), beats transient engine (`live_beats_transient_engine`), granular texture flux (`live_granular_texture_flux`), monitoring state control (`live_monitoring_state_control`), routing matrix config (`live_routing_matrix_config`), CPU meter inspector (`live_cpu_meter_inspector`), cue point navigator (`live_cue_point_navigator`), ~~track freeze control (`live_track_freeze_control`)~~ (proven impossible -- no freeze/flatten member on `Track`, v1.0.39 audit), clip pitch & RAM control (`live_clip_pitch_ram_control`), metronome & nudge control (`live_metronome_nudge_control`, partially shipped as `live_nudge` in v1.0.39) |
| **18. Browser & Viewport Automation** | Packs, Drum Pads, Dialogs & GUI | Browser tree query (`live_browser_tree_query`), hotswap target control (`live_hotswap_target_control`), drum pad copier (`live_drum_pad_copier`), dialog message handler (`live_dialog_message_handler`), GUI view visibility (`live_gui_view_visibility`), viewport zoom & scroll (`live_viewport_zoom_scroll`), song loop region control (`live_song_loop_region_control`), groove global amount (`live_groove_amount_control`), clip trigger quantization (`live_clip_trigger_quantization`), Simpler playback engine (`live_simpler_playback_engine`), note probability humanizer (`live_note_probability_humanizer`), exclusive arm & solo (`live_exclusive_arm_solo_control`), selected notes transform (`live_clip_selected_notes_transform`), appointed device control (`live_appointed_device_control`), audio clip scrub audition (`live_audio_clip_scrub_audition`) |

## 3. Reference Datasets on Drive B

1. **Vital Synth Headless Lab**:
   `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\vital_synth_headless_lab`
   * `INDEX.md`: Producer Pal routing table
   * `search.py`: BM25 full-text query CLI
   * `markdown/`: 10 modular chapters on Vital JSON schema, DawDreamer, and native Live translation.
2. **Ableton Racks Labeled**:
   `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton-racks-labeled`
   * `xml_presets/`: 134 production XML presets (Amps, Reverbs, Delays, Vocoders, Tape Strips).
   * `search.py`: BM25 full-text query CLI
   * `ableton_racks_labeled_chunks.jsonl`: Natural language prompts + engineering Chains-of-Thought.
3. **MixologyDB Mix Engineering**:
   `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\mixology_db`
   * `INDEX.md`: Producer Pal routing table
   * `search.py`: BM25 full-text query CLI
   * `raw_data/updated_tracks_full.json`: Raw 90 multitrack DAW projects (2,411 tracks, 2,177 evaluations).
   * `markdown/`: 10 modular chapters on empirical gain staging, parametric EQ Eight carving, and Mix Doctor critique rules.
4. **Ableton LiveAPI Tools & Remote Script Architecture**:
   `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_liveapi_tools`
   * `INDEX.md`: Producer Pal routing table
   * `search.py`: BM25 full-text query CLI
   * `raw_data/liveapi_tools.py`: Complete Python Remote Script implementation (220 tools, 44 categories).
   * `markdown/`: 10 modular chapters covering TCP architecture, grounded LOM boundaries, device control, CV Tools recipes, blueprints, and dual-engine bridge integration.
5. **AbletonMCP Extended Operations & Algorithmic Music Engine**:
   `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_mcp_extended`
   * `INDEX.md`: Producer Pal routing table
   * `search.py`: BM25 full-text query CLI
   * `raw_data/AbletonMCP_Remote_Script___init__.py`: Upstream v2.0.0+ remote script (307 KB, 257 commands).
   * `markdown/`: 10 modular chapters covering socket architecture, locators, Drum Rack 128-pad muting, Simpler reflection, 8 drum genres, 6 bassline styles, humanization, and dual-engine blueprints.
6. **Sound Similarity & Advanced Live Execution**:
   `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_live_mcp_bschoepke`
   * `INDEX.md`: Producer Pal routing table
   * `search.py`: BM25 full-text query CLI
   * `raw_data/similar_sounds.py`: Binary vector feature unpacker for `%LOCALAPPDATA%\Ableton\Live Database\Live-files-12300.db`.
   * `markdown/`: 10 modular chapters covering sound similarity search, arbitrary Python `live_exec`, Session-to-Arrangement stamping, automation curves, asynchronous property observation, and audio signal taps.
7. **AbletonBridge 359-Tool Suite & ASCII Grid Notation**:
   `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_bridge_hidingwill`
   * `INDEX.md`: Producer Pal routing table
   * `search.py`: BM25 full-text query CLI
   * `raw_data/`: Complete upstream suite (14 files, 359 tools across 15 modules, `grid_notation.py`, `creative.py`, `snapshots.py`, `m4l_bridge.js`).
   * `markdown/`: 10 modular chapters covering ASCII grid compilation, Euclidean rhythms, snapshot LERP morphing, sidechain routing, compound workflows, and deep M4L nested chain traversal.
8. **AbletonOSC Remote Script Suite & Full Session Dump**:
   `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\abletonosc_ideoforms`
   * `INDEX.md`: Producer Pal routing table
   * `search.py`: BM25 full-text query CLI
   * `raw_data/`: Complete upstream suite (19 files, `song.py`, `track.py`, `clip.py`, `device.py`, `midimap.py`, `client.py`).
   * `markdown/`: 10 modular chapters covering pure Python Remote Script Control Surface, UDP 11000/11001, 1-shot full session JSON dump, bulk multi-track queries, dynamic hardware MIDI CC mapping, track I/O routing, and real-time beat clock.
9. **PyLive Object-Oriented Python Client SDK**:
   `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\pylive_ideoforms`
   * `INDEX.md`: Producer Pal routing table
   * `search.py`: BM25 full-text query CLI
   * `raw_data/`: Complete upstream suite (19 files, `live/classes/*.py`, `live/query.py`, `examples/*.py`).
   * `markdown/`: 10 modular chapters covering object-oriented Python client SDK, `live.Set`, `live.Track`, `live.Clip`, ASCII session tree generator `set.dump()`, semantic lookups, beat-synchronized execution, stochastic clip walking, and sinusoidal tempo modulation.
10. **LiveRPyC Direct Memory Proxy & Zero-Protocol Execution**:
    `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\live_rpyc_lucianoiam`
    * `INDEX.md`: Producer Pal routing table
    * `search.py`: BM25 full-text query CLI
    * `raw_data/`: Complete upstream suite (10 files, `client.py`, `rpyc_server.py`, `rpyc_control_surface.py`, `lom_observer_helper.py`).
    * `markdown/`: 10 modular chapters covering RPyC Remote Python Call, direct LOM memory proxy `netref`, TCP port 17744, cross-process event listeners via `lom_observer_helper.py`, zero-protocol direct attribute manipulation, recursive rack/chain reflection, and native C++ `MidiNoteSpecification` injection.
11. **Ableton Live API Stub & Pre-Execution Validator**:
    `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_api_stub_cylab`
    * `INDEX.md`: Producer Pal routing table
    * `search.py`: BM25 full-text query CLI
    * `raw_data/`: Upstream source suite (`generate-stub.py`, `Live.xml`, `Live___init__.py`, `README.md`).
    * `markdown/`: 10 modular chapters covering Boost.Python XML schema, 100 pure-Python stub classes, offline `import Live`, static pre-execution LOM validation, docstring permissions, listenable event mapping, and enum translation.
12. **Ableton AI & Max 9 LOM Training Engine**:
    `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\ableton_ai_max9_lom_training`
    * `INDEX.md`: Producer Pal routing table
    * `search.py`: BM25 full-text query CLI
    * `raw_data/`: Upstream source suite (`Max9 LOM Reference.pdf`, `Max9 JS API Reference.pdf`, `Max9 NodeForMax API Reference.pdf`, `Remote_Scripts_Complete_Guide.md`, `Runtime_Changes_Live_11_to_12.md`, `Cycling74_Max_Reference_Guide.md`, `Cycling74_objects.json`).
    * `markdown/`: 16 modular chapters covering Remote Scripts v2/v3 framework, Live 11->12 runtime changes, Max 9 Live 12.3.5 LOM canonical paths, Meld/Roar/Drift device specialists, 74 native `abl.*` DSP algorithms, 36 `live.*` M4L objects, and Max 9 V8 / Node for Max `max-api` integration.
13. **Cycling '74 Max 1,805-Object Master Knowledgebase**:
    `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\cycling74_max_reference`
    * `INDEX.md`: Producer Pal routing table
    * `search.py`: BM25 full-text query CLI
    * `raw_data/`: Upstream source suite (`objects.json` with 1,805 objects, `guide.md` 73-page reference manual, `cycling74-reference-guide.pdf`).
    * `markdown/`: 14 modular chapters covering Core Max logic, MSP real-time audio, MC multi-channel polyphony, Gen~ JIT machine-code DSP, Jitter 3D/GLSL shaders, 74 native `abl.*` Live algorithms, and 36 `live.*` M4L objects.
14. **Live 12 MIDI Remote Scripts Reference (148 Controllers, v3 Framework & Cookbook)**:
    `B:\AI Directories_Databases\datasets\Music_Audio\Ableton Live Helper\live_12_remote_scripts_reference`
    * `INDEX.md`: Producer Pal routing table
    * `search.py`: BM25 full-text query CLI
    * `raw_data/`: Complete upstream suite (46 documents across 148 controllers, 15 Structure Void guides including Cookbook and 100 KB LOM map, `frameworks/ableton_v3.md`, `frameworks/system_frameworks.md`, `devices/novation_controllers.md`).
    * `markdown/`: 18 modular chapters covering Ableton v3 framework architecture, AutoArm & ActiveParameter components, Novation Launchkey MK4 Sysex protocols, PushBase engine, Akai touch faders, `_MxDCore` internal mechanics, Remote Script Cookbook recipes, and hierarchical LOM navigation.

---

## 4. Backlog: Future Additions (Add Incrementally)
- [ ] **Audio-to-Wavetable Resynthesizer**: Drop a 1-shot audio sample from Live, slice 2048-sample single cycles, and write out a new `.vitaltable`.
- [ ] **Multi-Band Parallel FX Splitter Tool**: Dedicated 1-click action to create a 3-way (Low/Mid/High) crossover rack for any audio effect.
- [ ] **Microtuning / Scala (.scl) Exporter**: Inject custom microtonal scales into generated `.vital` presets.
- [ ] **Multi-Clip Batch Baker**: Select multiple scenes or clips across tracks and render all stems in parallel into a stem folder.
- [ ] **LUFS / True-Peak Master Bus Limiter Normalizer**: Automated final gain adjustment targeting -14 LUFS integrated for streaming.
- [ ] **TCP Browser Item Proxy**: Background daemon in `helper.py` that listens for bridge browser load requests and transparently forwards them to `AbletonMCP` on port 9877.
