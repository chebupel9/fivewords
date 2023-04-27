<?php
header('Content-Type: application/json');
$words_array = ['бычок', 'векша', 'водка', 'вязья', 'голос', 'горшь', 'дубок', 'жизнь', 'замок', 'зерно', 'злаки', 'излом', 'клещи', 'косой', 'крыша', 'лазер', 'ледок', 'лимон', 'метла', 'мечта', 'минус', 'мозги', 'мотор', 'налет', 'нужда', 'обвал', 'озера', 'осень', 'ответ', 'охота', 'папка', 'парус', 'пером'];
$word = $words_array[array_rand($words_array)];

session_start();

function check($word, $submitted_word) {
    mb_internal_encoding('UTF-8');
    $answer = array();
    for ($i=0; $i<5; $i++) {
       if (mb_substr($word, $i, 1, 'UTF-8') == mb_substr($submitted_word, $i, 1, 'UTF-8')) {
          $answer[$i] = '<div class="square mx-2"><h4 class="green">' . mb_substr($submitted_word, $i, 1, 'UTF-8') . '</h4></div>';
       } elseif (mb_strpos($word, mb_substr($submitted_word, $i, 1, 'UTF-8')) !== false) {
          $answer[$i] = '<div class="square mx-2"><h4 class="yellow">' . mb_substr($submitted_word, $i, 1, 'UTF-8') . '</h4></div>';
       } else {
          $answer[$i] = '<div class="square mx-2"><h4 class="grey">' . mb_substr($submitted_word, $i, 1, 'UTF-8') . '</h4></div>';
       }
    }
    $result = '';
    for ($i=0; $i<count($answer); $i++) {
       $result = $result . $answer[$i];
    }
    return $result;
}

if (!isset($_SESSION['count'])) {
    $_SESSION['count'] = 0;
    $_SESSION['word'] = $words_array[array_rand($words_array)];
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $_SESSION['test'] = $_POST['message'];
    if ($_SESSION['test'] === 'reload') {
        $_SESSION['count'] = 0;
        $_SESSION['word'] = $words_array[array_rand($words_array)];
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $_SESSION['submitted_word'] = $_POST['name'] ?? '';
    if ($_SESSION['submitted_word'] === $_SESSION['word']) {
        $_SESSION['guessed'] = 'VICTORY';
        $_SESSION['id'] = $_SESSION['count']+1;
        $_SESSION['count'] = 0;
        $result = check($_SESSION['word'], $_SESSION['submitted_word']);
        $_SESSION['answer'] = $result;
        echo json_encode(['answer' => $_SESSION['answer'], 'message' => $_SESSION['guessed'], 'count' => 'Попыток: ' . $_SESSION['count'], 'word' => '<div class="answer-box">' . $_SESSION['word'] . '</div>', 'id' => $_SESSION['id']]);
        session_destroy();
        exit;
    } else {
        if ($_SESSION['submitted_word'] === '' || strlen($_SESSION['submitted_word']) > 10 || strlen($_SESSION['submitted_word']) < 10) {
            $_SESSION['guessed'] = 'ERROR_SYMBOL';
            $_SESSION['answer'] = '';
            echo json_encode(['answer' => $_SESSION['answer'], 'message' => $_SESSION['guessed'], 'count' => 'Попыток: ' . 5-$_SESSION['count'], 'id' => $_SESSION['count']]);
            exit;
        } else {
            $_SESSION['count']++;
            if ($_SESSION['count'] >= 5) {
                $_SESSION['guessed'] = 'FAIL';
                $_SESSION['id'] = 5;
                $_SESSION['count'] = 0;
                $result = check($_SESSION['word'], $_SESSION['submitted_word']);
                $_SESSION['answer'] = $result;
                echo json_encode(['answer' => $_SESSION['answer'],'message' => $_SESSION['guessed'], 'count' => 'Попыток: ' . $_SESSION['count'], 'word' => '<div class="answer-box">' . $_SESSION['word'] . '</div>', 'id' => $_SESSION['id']]);
                session_destroy();
                exit;
            } else {
                $_SESSION['guessed'] = 'FALSE';
                $result = check($_SESSION['word'], $_SESSION['submitted_word']);
                $_SESSION['answer'] = $result;
                echo json_encode(['answer' => $_SESSION['answer'], 'message' => $_SESSION['guessed'], 'count' => 'Попыток: ' . 5-$_SESSION['count'], 'id' => $_SESSION['count']]);
            }
        }
    }
}
?>