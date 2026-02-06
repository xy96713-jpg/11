import * as THREE from 'three';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';
import { FontLoader } from 'three/addons/loaders/FontLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';

let scene, camera, renderer, composer, clock;
let gridPlane, textGroup;
const COLORS = { phosphor: 0x64ff64, bg: 0x000200 };

async function init() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(COLORS.bg);
    scene.fog = new THREE.Fog(COLORS.bg, 2, 15);

    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 1.5, 6);

    const container = document.getElementById('scene-container');
    renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    clock = new THREE.Clock();
    textGroup = new THREE.Group();
    scene.add(textGroup);

    // 1. Retro Infinite Grid (S09 Logic)
    const gridSize = 40;
    const gridDivisions = 40;
    gridPlane = new THREE.GridHelper(gridSize, gridDivisions, COLORS.phosphor, 0x111111);
    gridPlane.position.y = -1;
    scene.add(gridPlane);

    // 2. 3D Euiyo Typography
    const loader = new FontLoader();
    loader.load('https://unpkg.com/three@0.160.0/examples/fonts/helvetiker_bold.typeface.json', (font) => {
        const mat = new THREE.MeshBasicMaterial({ color: COLORS.phosphor, wireframe: true });

        const textGeo = new TextGeometry('euiyo', { font, size: 1.5, height: 0.4, curveSegments: 2 });
        textGeo.center();
        const mesh = new THREE.Mesh(textGeo, mat);
        textGroup.add(mesh);

        const videoGeo = new TextGeometry('VIDEO', { font, size: 0.3, height: 0.1 });
        videoGeo.center();
        const vMesh = new THREE.Mesh(videoGeo, mat);
        vMesh.position.y = -1.2;
        textGroup.add(vMesh);
    });

    // 3. Post-Processing: Chromatic Aberration, Scanlines & Pixelation (The euiyo Core)
    composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));

    const EuiyoShader = {
        uniforms: {
            "tDiffuse": { value: null },
            "time": { value: 0.0 },
            "pixelSize": { value: 6.0 }, // S05 Style: Large pixels for retro feel
            "noiseAmount": { value: 0.05 }
        },
        vertexShader: `
            varying vec2 vUv;
            void main() {
                vUv = uv;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform sampler2D tDiffuse;
            uniform float time;
            uniform float pixelSize;
            uniform float noiseAmount;
            varying vec2 vUv;

            float rand(vec2 n) { 
                return fract(sin(dot(n, vec2(12.9898, 4.1414))) * 43758.5453);
            }

            void main() {
                // 1. Pixelation (S09 Arch Logic)
                vec2 res = vec2(textureSize(tDiffuse, 0));
                vec2 pUv = floor(vUv * res / pixelSize) * pixelSize / res;

                // 2. Chromatic Aberration with Jitter
                float jitter = (rand(vec2(time, time)) - 0.5) * 0.01;
                float offset = 0.005 + jitter;
                
                vec4 cr = texture2D(tDiffuse, pUv + vec2(offset, 0.0));
                vec4 cg = texture2D(tDiffuse, pUv);
                vec4 cb = texture2D(tDiffuse, pUv - vec2(offset, 0.0));
                
                vec4 color = vec4(cr.r, cg.g, cb.b, cg.a);
                
                // 3. Scanlines
                float s = sin(pUv.y * res.y * 0.5 + time * 10.0);
                color.rgb -= s * 0.08;

                // 4. Digital Noise
                color.rgb += (rand(pUv + time) - 0.5) * noiseAmount;

                // 5. Screen Flicker (S00 PM Preference: High tension)
                color.rgb *= 0.95 + 0.05 * sin(120.0 * time);

                // 6. Phosphor Tint
                color.rgb *= vec3(0.9, 1.1, 0.9);

                gl_FragColor = color;
            }
        `
    };

    const glitchPass = new ShaderPass(EuiyoShader);
    composer.addPass(glitchPass);

    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
        composer.setSize(container.clientWidth, container.clientHeight);
    });

    animate();
}

function animate() {
    requestAnimationFrame(animate);
    const time = clock.getElapsedTime();

    if (gridPlane) {
        // Precise math calculation (Skill 09)
        gridPlane.position.z = (time * 1.5) % 2;
    }

    if (textGroup) {
        // Floating motion
        textGroup.rotation.y = Math.sin(time * 0.4) * 0.15;
        textGroup.position.y = Math.sin(time * 1.5) * 0.05;

        // Sudden "Digital Glitch" Jumps (PM Persona: Unpredictable)
        if (Math.random() > 0.98) {
            textGroup.position.x = (Math.random() - 0.5) * 0.3;
            textGroup.rotation.z = (Math.random() - 0.5) * 0.05;
        } else {
            textGroup.position.x *= 0.85;
            textGroup.rotation.z *= 0.85;
        }

        // Wireframe pulsing
        textGroup.children.forEach(mesh => {
            mesh.material.opacity = 0.8 + 0.2 * Math.sin(time * 10.0);
        });
    }

    if (composer) {
        composer.passes[1].uniforms.time.value = time;
        composer.render();
    }
}

init();
