<?php
$films = ["Inception", "Interstellar", "Mr Robot", "The Social Network", "Shutter Island"];

echo "Le troisième film est : " . $films[2] . "<br>";

echo "Liste des films :<br>";
foreach ($films as $film) {
    echo $film . "<br>";
}

echo "<hr>";

$livre = [
    "titre" => "The Rational Male",
    "auteur" => "Rollo Tomassi",
    "annee_publication" => 2013,
    "genre" => "Masculine Book"
];

echo "Livre : " . $livre["titre"] . " par " . $livre["auteur"] . "<br>";

echo "Détails du livre :<br>";
foreach ($livre as $cle => $valeur) {
    echo $cle . " : " . $valeur . "<br>";
}

echo "<hr>";

$etudiants = [
    [
        "nom" => "Es-salehy",
        "prenom" => "Aymane",
        "notes" => [18, 16, 14]
    ],
    [
        "nom" => "Amamou",
        "prenom" => "Ahmed",
        "notes" => [18, 20, 19]
    ],
    [
        "nom" => "El-Arfaouy",
        "prenom" => "Noureddine",
        "notes" => [10, 13, 11]
    ]
];

echo "Deuxième étudiant : " . $etudiants[1]["prenom"] . " " . $etudiants[1]["nom"] . "<br>";

echo "Première note du premier étudiant : " . $etudiants[0]["notes"][0] . "<br>";

echo "Moyennes des étudiants :<br>";
foreach ($etudiants as $etu) {
    $moyenne = array_sum($etu["notes"]) / count($etu["notes"]);
    echo $etu["prenom"] . " " . $etu["nom"] . " : Moyenne = " . $moyenne . "<br>";
}
?>
