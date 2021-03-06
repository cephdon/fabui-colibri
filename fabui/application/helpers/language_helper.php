<?php
/**
 * 
 * @author Krios Mane
 * @version 0.1
 * @license https://opensource.org/licenses/GPL-3.0
 * 
 */
 ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
if(!function_exists('getAvailableLanguages'))
{
	/**
	 * Get available languages
	 *
	 * Get a list of available languages.
	 * 
	 * @return	list Array
	 */
	function getAvailableLanguages()
	{
		$ini = parse_ini_file("/var/lib/fabui/lang.ini", true);
		unset($ini['language']);
		return $ini;
	}
}
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
if(!function_exists('langauges_menu'))
{
	/**
	 * Languages Menu
	 *
	 * Generates a drop-down menu of available languages.
	 *
	 * @param	string	classname
	 * @param	string	menu name
	 * @param	mixed	attributes
	 * @return	string
	 */
	function langauges_menu($class = '', $name = 'languages', $attributes = '', $selected = '')
	{
		$languages = getAvailableLanguages();		
		$html = '<select class="'.$class.'" name="'.$name.'" '._stringify_attributes($attributes).'>';
		foreach($languages as $name => $lang){
			$sel = $selected == $lang['code'] ? 'selected="selected"' : '';
			$html .= '<option '.$sel.' value="'.$lang['code'].'">'.$lang['description'].'</option>';
		}
		$html .= '</select>';
		return $html;
	}
}
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
if(!function_exists('setLanguage'))
{
	/**
	 * 
	 */
	function setLanguage($language_code, $saveSettings=false)
	{
		$CI =& get_instance();
		$CI->config->load('fabtotum');
		$CI->load->helper(array('plugin_helper', 'fabtotum_helper'));
		
		putenv('LC_MESSAGES='.$language_code.'.UTF-8');
		setlocale(LC_MESSAGES, $language_code.'.UTF-8');
		
		// Set numeric format to en_US as it uses dot '.' as decimal separator
		putenv('LC_NUMERIC='.'en_US.UTF-8');
		setlocale(LC_NUMERIC, 'en_US.UTF-8');
		
		bindtextdomain("fabui", $CI->config->item('locale_path'));
		textdomain("fabui");
		bind_textdomain_codeset("fabui", "UTF-8");
		
		if($saveSettings == true){
		  $hardwareSettings = loadSettings();
		  $hardwareSettings['locale'] = $language_code;
		  saveSettings($hardwareSettings);
		}
		
		//extendLanguageWithPlugins();
	}
}
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
if(!function_exists('getCurrentLanguage'))
{
	/**
	 * 
	 */
	function getCurrentLanguage()
	{
	    $CI =& get_instance();
    	$CI->load->helper('fabtotum_helper');
    	$settings = loadSettings();
    	
    	if(isset($settings['locale']))
    		return $settings['locale'];
    	else
    		return 'en_US';
	}
}
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
if(!function_exists('loadTranslation'))
{
	/**
	 * 
	 */
	function loadTranslation()
	{	
		$language_code = getCurrentLanguage();
		setLanguage($language_code);
	}
}
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
if(!function_exists('getJsonTranslation'))
{
	/**
	 * 
	 */
	function getJsonTranslation()
	{
		$CI =& get_instance();
		$CI->config->load('fabtotum');
		
		$language_code = getCurrentLanguage();
		$language_code_short = explode('_', $language_code)[0];
		
		$filename = $CI->config->item('locale_path') . $language_code_short . '/LC_MESSAGES/fabui.json';
		
		if( file_exists($filename) )
		{
			return file_get_contents($filename);
		}
		else
		{
			return '{}';
		}
	}
}
 ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
if(!function_exists('pyformat'))
{
	function pyformat($fmt, $args)
	{
		foreach($args as $i => $arg_val)
		{
			$arg_sym = '{' .$i. '}';
			$fmt = str_replace($arg_sym, $arg_val, $fmt);
		}

		return $fmt;
	}
}
?>
