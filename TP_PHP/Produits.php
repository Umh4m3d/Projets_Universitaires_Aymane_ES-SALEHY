<?php
$host = 'localhost';
$dbname = 'ecommerce_securise_db';
$username = 'app_ecommerce';
$password = 'test.1234';

try {

    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Erreur de connexion à la base de données...");
}

$sql = "SELECT * FROM Produits";
$stmt = $pdo->query($sql);
$produits = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>

<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Liste des Produits</title>
</head>
<body>
    <h1>Nos Produits</h1>
    <div class="container">
        <?php foreach ($produits as $produit): ?>
            <div class="produit-card">
                <h3> -- <?php echo htmlspecialchars($produit['nom']); ?> --</h3>
                <strong>Description: </strong><?php echo htmlspecialchars($produit['description']); ?>
                <br>
                <strong>Prix: </strong> <?php echo htmlspecialchars($produit['prix']); ?> MAD
            </div>
        <?php endforeach; ?>
    </div>
</body>
</html>
