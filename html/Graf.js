import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

// Инициализация сцены, камеры и рендера
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Управление камерой
const controls = new OrbitControls(camera, renderer.domElement);

// Глобус
const globeGeometry = new THREE.SphereGeometry(1, 64, 64);
const globeTexture = new THREE.TextureLoader().load('path_to_earth_texture.jpg'); // Текстура Земли
const globeMaterial = new THREE.MeshStandardMaterial({ map: globeTexture });
const globe = new THREE.Mesh(globeGeometry, globeMaterial);
scene.add(globe);

// Атмосфера
const atmosphereGeometry = new THREE.SphereGeometry(1.02, 64, 64);
const atmosphereMaterial = new THREE.MeshBasicMaterial({
    color: 0x00aaff,
    transparent: true,
    opacity: 0.1,
});
const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
scene.add(atmosphere);

// Освещение
const light = new THREE.PointLight(0xffffff, 1);
light.position.set(5, 5, 5);
scene.add(light);

camera.position.set(3, 3, 3);
controls.update();

// Массив орбитальных спутников
const satellites = [];

/**
 * Функция создания орбиты
 * @param {number} semiMajorAxis - Большая полуось орбиты
 * @param {number} eccentricity - Эксцентриситет орбиты (0 для круглой орбиты)
 * @param {number} inclination - Наклонение орбиты (в градусах)
 * @param {number} longitudeOfAscendingNode - Долгота восходящего узла (в градусах)
 */
function createOrbit(semiMajorAxis, eccentricity, inclination, longitudeOfAscendingNode) {
    const semiMinorAxis = semiMajorAxis * Math.sqrt(1 - eccentricity ** 2);
    const curve = new THREE.EllipseCurve(
        0, 0, // Центр
        semiMajorAxis, semiMinorAxis // Большая и малая полуоси
    );
    const points = curve.getPoints(100);
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({ color: 0xff0000 });
    const orbit = new THREE.Line(geometry, material);

    // Применение наклона и ориентации орбиты
    orbit.rotation.x = THREE.MathUtils.degToRad(inclination); // Наклонение
    orbit.rotation.z = THREE.MathUtils.degToRad(longitudeOfAscendingNode); // Долгота восходящего узла

    scene.add(orbit);

    // Добавление спутника
    const satelliteGeometry = new THREE.SphereGeometry(0.05, 16, 16);
    const satelliteMaterial = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
    const satellite = new THREE.Mesh(satelliteGeometry, satelliteMaterial);

    satellite.userData = {
        orbitRadius: semiMajorAxis,
        semiMinorAxis: semiMinorAxis,
        angle: 0,
        inclination: inclination,
        longitudeOfAscendingNode: longitudeOfAscendingNode,
    };

    satellites.push(satellite);
    scene.add(satellite);
}

// Пример: Добавление орбит
createOrbit(1.5, 0.2, 45, 30); // Полуось, эксцентриситет, наклон, долгота узла
createOrbit(2.0, 0.1, 30, 60);

/**
 * Анимация спутников
 */
function animateSatellites() {
    satellites.forEach((satellite) => {
        const { orbitRadius, semiMinorAxis, angle, inclination, longitudeOfAscendingNode } = satellite.userData;
        satellite.userData.angle += 0.01; // Угол движения

        // Вычисление положения спутника
        const x = orbitRadius * Math.cos(satellite.userData.angle);
        const z = semiMinorAxis * Math.sin(satellite.userData.angle);

        // Применение ориентации орбиты
        const position = new THREE.Vector3(x, 0, z);
        position.applyAxisAngle(new THREE.Vector3(0, 0, 1), THREE.MathUtils.degToRad(longitudeOfAscendingNode));
        position.applyAxisAngle(new THREE.Vector3(1, 0, 0), THREE.MathUtils.degToRad(inclination));

        satellite.position.set(position.x, position.y, position.z);
    });
}

// Анимация
function animate() {
    requestAnimationFrame(animate);

    // Вращение глобуса
    globe.rotation.y += 0.001;

    // Анимация спутников
    animateSatellites();

    // Рендеринг сцены
    renderer.render(scene, camera);
}

animate();
