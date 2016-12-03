<?php namespace Helpers;
// Set UTF-8 as the default encoding
mb_internal_encoding("UTF-8");

class UTF8 {

	public static function string_to_array($string) {

		// multibyte string split
		$list = [];

		for ($i = 0; $i < mb_strlen($string); $i++ ) {
		    $list[] = mb_substr($string, $i, 1);
		}

		return $list;
	}

	public static function char_in_string($char, $string) {
		
		$list = self::string_to_array($string);

		foreach ($list as $singleChar) {

			$singleChar = mb_strtoupper((utf8_encode($singleChar)));
			$char = mb_strtoupper((utf8_encode($char)));

			if (strcmp($singleChar, $char) == 0) {
				return true;
				break;
			}
		}

		return false;
	}

	/**
	 * Replace all occurrences of the search string with the replacement string. Multibyte safe.
	 * http://stackoverflow.com/questions/3489495/mb-str-replace-is-slow-any-alternatives
	 *
	 * @param string|array $search The value being searched for, otherwise known as the needle. An array may be used to designate multiple needles.
	 * @param string|array $replace The replacement value that replaces found search values. An array may be used to designate multiple replacements.
	 * @param string|array $subject The string or array being searched and replaced on, otherwise known as the haystack.
	 *                              If subject is an array, then the search and replace is performed with every entry of subject, and the return value is an array as well.
	 * @param string $encoding The encoding parameter is the character encoding. If it is omitted, the internal character encoding value will be used.
	 * @param int $count If passed, this will be set to the number of replacements performed.
	 * @return array|string
	 */
	public static function replace($search, $replace, $subject, $encoding = 'auto', &$count=0) {
	    if(!is_array($subject)) {
	        $searches = is_array($search) ? array_values($search) : [$search];
	        $replacements = is_array($replace) ? array_values($replace) : [$replace];
	        $replacements = array_pad($replacements, count($searches), '');
	        foreach($searches as $key => $search) {
	            $replace = $replacements[$key];
	            $search_len = mb_strlen($search, $encoding);

	            $sb = [];
	            while(($offset = mb_strpos($subject, $search, 0, $encoding)) !== false) {
	                $sb[] = mb_substr($subject, 0, $offset, $encoding);
	                $subject = mb_substr($subject, $offset + $search_len, null, $encoding);
	                ++$count;
	            }
	            $sb[] = $subject;
	            $subject = implode($replace, $sb);
	        }
	    } else {
	        foreach($subject as $key => $value) {
	            $subject[$key] = self::replace($search, $replace, $value, $encoding, $count);
	        }
	    }
	    return $subject;
	}
}